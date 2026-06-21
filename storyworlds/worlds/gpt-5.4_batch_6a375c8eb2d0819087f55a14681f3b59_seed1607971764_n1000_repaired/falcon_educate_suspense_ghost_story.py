#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py
=================================================================

A standalone storyworld for a child-facing suspense tale told in a gentle
ghost-story style: a child hears eerie sounds in an old place, fears a ghost,
then learns that a real falcon family made the strange cries and shadows.

The world model tracks physical state (light, echo, nest signs, distance) and
emotional state (fear, courage, relief, curiosity, trust, learning). The prose
is driven by stateful beats: an eerie setup, a mistaken ghost fear, a careful
investigation, a natural explanation, and a warm educational ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --place bell_tower
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --weather stormy
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/falcon_educate_suspense_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "caretaker_woman", "ranger_woman"}
        male = {"boy", "father", "man", "caretaker_man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")


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
class Place:
    id: str
    label: str
    opening: str
    dark_spot: str
    echo_text: str
    climb_text: str
    reveal_view: str
    supports: set[str] = field(default_factory=set)
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
class Weather:
    id: str
    opening: str
    sound_color: str
    light_text: str
    fear_boost: int
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
class Sign:
    id: str
    label: str
    found_text: str
    explains: set[str] = field(default_factory=set)
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
class Lesson:
    id: str
    label: str
    teach_text: str
    ending_text: str
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
class AdultRole:
    id: str
    label: str
    type: str
    arrive_text: str
    knows_text: str
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


PLACES = {
    "bell_tower": Place(
        id="bell_tower",
        label="old bell tower",
        opening="At the edge of the village stood an old bell tower with narrow stairs and a round black window high above.",
        dark_spot="the landing below the bell room",
        echo_text="Every small scrape came back as a bigger sound from the stone walls.",
        climb_text="The steps curled upward like a gray shell, and each turn hid the next one.",
        reveal_view="In the cracked bell room, moonlight brushed a nest tucked behind a beam.",
        supports={"feather", "whitewash", "nest_twigs"},
        tags={"tower", "stone"},
    ),
    "chapel_roof": Place(
        id="chapel_roof",
        label="old chapel loft",
        opening="Behind the little chapel was a loft under the roof, all old wood, beams, and moon-pale dust.",
        dark_spot="the loft above the rafters",
        echo_text="The rafters clicked and whispered whenever the wind pressed at the roof.",
        climb_text="A ladder rose into the dark, and the dark seemed to wait at the top.",
        reveal_view="Up among the rafters, a neat nest rested in a corner where the moon could slip in.",
        supports={"feather", "nest_twigs"},
        tags={"roof", "wood"},
    ),
    "mill_loft": Place(
        id="mill_loft",
        label="old mill loft",
        opening="Near the river stood an old mill loft with empty grain bins and slanted boards that creaked under small feet.",
        dark_spot="the loft above the empty bins",
        echo_text="Loose boards answered each footstep with hollow knocks.",
        climb_text="The children followed a steep ladder, and the shadows shifted between the beams.",
        reveal_view="At the top, behind a wheel beam, there was a nest lined with soft down.",
        supports={"feather", "whitewash", "nest_twigs"},
        tags={"mill", "wood"},
    ),
}

WEATHERS = {
    "misty": Weather(
        id="misty",
        opening="Mist had wrapped the yard so softly that even the fence posts looked like sleepy strangers.",
        sound_color="The air carried every cry in a thin, floaty way that made near things sound far and far things sound near.",
        light_text="The moon was a pale coin behind the mist.",
        fear_boost=1,
        tags={"mist"},
    ),
    "windy": Weather(
        id="windy",
        opening="A restless wind moved around the eaves and made the shutters tap, tap, tap.",
        sound_color="Each gust pushed strange whistles through cracks and corners.",
        light_text="Clouds sailed past the moon and kept dimming the light.",
        fear_boost=1,
        tags={"wind"},
    ),
    "stormy": Weather(
        id="stormy",
        opening="Far thunder grumbled now and then, and the night kept folding itself darker between flashes of light.",
        sound_color="The storm threw sharp sounds across the roof and swallowed the soft ones.",
        light_text="Whenever lightning blinked, every beam and stair jumped out and vanished again.",
        fear_boost=2,
        tags={"storm"},
    ),
}

SIGNS = {
    "feather": Sign(
        id="feather",
        label="striped feather",
        found_text="On the stair lay a striped feather, long and clean, not at all like anything a ghost would leave behind.",
        explains={"bell_tower", "chapel_roof", "mill_loft"},
        tags={"feather", "bird"},
    ),
    "whitewash": Sign(
        id="whitewash",
        label="white splash on the boards",
        found_text="By the beam was a chalky white splash, the kind birds leave where they perch again and again.",
        explains={"bell_tower", "mill_loft"},
        tags={"bird_sign"},
    ),
    "nest_twigs": Sign(
        id="nest_twigs",
        label="little nest of twigs",
        found_text="Tucked in a corner were twigs and soft fluff woven into a little nest.",
        explains={"bell_tower", "chapel_roof", "mill_loft"},
        tags={"nest", "bird"},
    ),
}

LESSONS = {
    "quiet_watch": Lesson(
        id="quiet_watch",
        label="quiet watch",
        teach_text="The adult explained that a falcon is a fast hunting bird, not a ghost at all, and that the nest had to stay calm and safe.",
        ending_text="They watched in still silence until the falcon skimmed past the window like a living arrow.",
        tags={"falcon", "watch"},
    ),
    "field_guide": Lesson(
        id="field_guide",
        label="field guide",
        teach_text="The adult opened a little bird guide and used it to educate the children about falcon wings, hooked beaks, and sharp eyes.",
        ending_text="By the end, the page in the guide looked less like a lesson and more like a secret they were glad to know.",
        tags={"falcon", "educate", "book"},
    ),
    "nest_rule": Lesson(
        id="nest_rule",
        label="nest rule",
        teach_text="The adult said the best way to educate a brave mind is to replace a spooky guess with careful noticing, then added that nesting falcons need space.",
        ending_text="So the children stepped back softly, keeping the nest safe while their fear melted into wonder.",
        tags={"falcon", "educate", "nest"},
    ),
}

ADULTS = {
    "teacher": AdultRole(
        id="teacher",
        label="teacher",
        type="teacher",
        arrive_text="Their teacher came with a lamp and a voice so steady that the dark stopped feeling quite so large.",
        knows_text="She knew the old building well and listened before she spoke.",
        tags={"school", "educate"},
    ),
    "caretaker": AdultRole(
        id="caretaker",
        label="caretaker",
        type="caretaker_man",
        arrive_text="The old caretaker arrived with a lantern, its warm circle of light sliding over the stairs.",
        knows_text="He had watched the building through many seasons and knew what nested in its hidden places.",
        tags={"caretaker", "lantern"},
    ),
    "ranger": AdultRole(
        id="ranger",
        label="ranger",
        type="ranger_woman",
        arrive_text="A park ranger stepped in from the yard with a hooded lamp and mud on her boots.",
        knows_text="She listened to the cries above them with a calm, knowing smile.",
        tags={"ranger", "educate"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Elsie", "Wren", "Ivy", "Clara"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Eli", "Noah", "Finn", "Owen", "Jude"]
TRAITS = ["curious", "careful", "thoughtful", "brave", "quiet", "gentle"]


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


def _r_echo_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    place = world.get("place")
    if hero.meters["heard_cry"] >= THRESHOLD and place.meters["darkness"] >= THRESHOLD:
        sig = ("echo_fear", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_sign_curiosity(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sign = world.get("sign")
    if sign.meters["seen"] >= THRESHOLD:
        sig = ("sign_curiosity", sign.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["curiosity"] += 1
            out.append("__curiosity__")
    return out


def _r_lamp_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    adult = world.get("adult")
    if adult.meters["near"] >= THRESHOLD and adult.meters["lamp_on"] >= THRESHOLD:
        sig = ("lamp_calm", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
            hero.memes["trust"] += 1
            out.append("__calm__")
    return out


def _r_reveal_learning(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    falcon = world.get("falcon")
    if falcon.meters["seen"] >= THRESHOLD:
        sig = ("reveal_learning", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["wonder"] += 1
            hero.memes["learning"] += 1
            out.append("__learning__")
    return out


CAUSAL_RULES = [
    Rule(name="echo_fear", tag="emotion", apply=_r_echo_fear),
    Rule(name="sign_curiosity", tag="emotion", apply=_r_sign_curiosity),
    Rule(name="lamp_calm", tag="emotion", apply=_r_lamp_calm),
    Rule(name="reveal_learning", tag="emotion", apply=_r_reveal_learning),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combo(place_id: str, sign_id: str) -> bool:
    return sign_id in PLACES[place_id].supports and place_id in SIGNS[sign_id].explains


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in sorted(PLACES):
        for sign_id in sorted(SIGNS):
            if valid_combo(place_id, sign_id):
                combos.append((place_id, sign_id))
    return combos


def fear_level(weather_id: str, trait: str) -> int:
    base = WEATHERS[weather_id].fear_boost
    if trait in {"careful", "quiet"}:
        base += 1
    if trait == "brave":
        base -= 1
    return max(0, base)


def would_climb(weather_id: str, trait: str) -> bool:
    return fear_level(weather_id, trait) <= 1


def outcome_of(params: "StoryParams") -> str:
    return "climb" if would_climb(params.weather, params.trait) else "call"


def explain_rejection(place_id: str, sign_id: str) -> str:
    place = PLACES[place_id]
    sign = SIGNS[sign_id]
    return (
        f"(No story: {sign.label} is not a sensible clue for the {place.label}. "
        f"The sign must fit the place where the falcon could really nest.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_is_ghost(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    place = sim.get("place")
    hero.meters["heard_cry"] += 1
    place.meters["darkness"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": hero.memes["fear"],
        "looks_like_ghost": hero.memes["fear"] >= THRESHOLD and sim.facts.get("falcon_seen", False) is False,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, place: Place, weather: Weather) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{place.opening} {weather.opening}"
    )
    world.say(
        f"That evening, {hero.id} and {friend.id} lingered nearby because they loved old stories and dared each other to be the last one still listening."
    )


def first_sound(world: World, hero: Entity, friend: Entity, place: Place, weather: Weather) -> None:
    hero.meters["heard_cry"] += 1
    friend.meters["heard_cry"] += 1
    world.get("place").meters["darkness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From {place.dark_spot} came a thin, falling cry. {weather.sound_color} {place.echo_text}"
    )
    world.say(
        f'{friend.id} grabbed {hero.id}\'s sleeve. "Did you hear that?"'
    )
    world.say(
        f"{hero.id} listened again, and for one chilly moment the sound did seem like a ghost calling from inside the walls."
    )


def ghost_guess(world: World, hero: Entity, place: Place, weather: Weather) -> None:
    pred = predict_is_ghost(world)
    world.facts["predicted_fear"] = pred["fear"]
    hero.memes["imagination"] += 1
    line = f'{hero.id} whispered, "Maybe this place is haunted."'
    if weather.id == "stormy":
        line += " Lightning blinked, and the stairs looked full of hiding shapes."
    world.say(line)


def choose_path(world: World, hero: Entity, friend: Entity, place: Place, weather: Weather, climb: bool) -> None:
    if climb:
        hero.memes["courage"] += 1
        friend.memes["trust"] += 1
        world.say(
            f"But {hero.id}'s curiosity was tugging just as hard as fear. Holding hands, the two children took one slow step toward {place.dark_spot}."
        )
        world.say(place.climb_text)
    else:
        hero.memes["caution"] += 1
        friend.memes["caution"] += 1
        world.say(
            f"The cry came again, sharper this time, and both children stopped where they were. It felt wiser to stay together at the bottom and call for help instead of climbing alone."
        )


def find_sign(world: World, hero: Entity, sign: Sign) -> None:
    world.get("sign").meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(sign.found_text)
    if hero.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"That small clue poked a neat little hole in the ghost idea."
        )


def call_adult(world: World, adult: Entity, adult_cfg: AdultRole) -> None:
    adult.meters["near"] += 1
    adult.meters["lamp_on"] += 1
    propagate(world, narrate=False)
    world.say(adult_cfg.arrive_text)
    world.say(adult_cfg.knows_text)


def reveal(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    falcon = world.get("falcon")
    falcon.meters["seen"] += 1
    world.facts["falcon_seen"] = True
    propagate(world, narrate=False)
    world.say(place.reveal_view)
    world.say(
        "Then a shadow moved. Not a floating ghost at all, but a real bird with bright eyes and folded wings."
    )
    world.say(
        "When it shifted, its hooked beak showed in the lamp glow, and the strange cry finally made sense."
    )
    hero.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0


def educate(world: World, adult: Entity, lesson: Lesson) -> None:
    world.say(
        f'{adult.label_word.capitalize()} smiled gently. "{lesson.teach_text}"'
    )
    if "educate" in lesson.tags or "educate" in ADULTS[world.facts["adult_cfg"].id].tags:
        world.say(
            "Instead of hurrying the children away, the adult chose to educate them, showing how careful looking can turn a scary guess into the truth."
        )


def ending(world: World, hero: Entity, friend: Entity, lesson: Lesson) -> None:
    hero.memes["safety"] += 1
    friend.memes["safety"] += 1
    world.say(lesson.ending_text)
    world.say(
        f"On the way home, {friend.id} no longer called the building haunted. {hero.id} kept whispering one new word with a smile: falcon."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    weather: Weather,
    sign: Sign,
    lesson: Lesson,
    adult_cfg: AdultRole,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["loyal"],
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_cfg.type,
        label=adult_cfg.label,
        role="adult",
        attrs={"profession": adult_cfg.label},
    ))
    world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
    ))
    world.add(Entity(
        id="sign",
        kind="thing",
        type="clue",
        label=sign.label,
    ))
    world.add(Entity(
        id="falcon",
        kind="thing",
        type="falcon",
        label="falcon",
        attrs={"nested": True},
    ))

    world.facts.update(
        place_cfg=place,
        weather_cfg=weather,
        sign_cfg=sign,
        lesson_cfg=lesson,
        adult_cfg=adult_cfg,
        hero=hero,
        friend=friend,
        adult=adult,
        falcon_seen=False,
        outcome="",
    )

    introduce(world, hero, friend, place, weather)
    world.para()
    first_sound(world, hero, friend, place, weather)
    ghost_guess(world, hero, place, weather)
    climb = would_climb(weather.id, trait)
    choose_path(world, hero, friend, place, weather, climb)
    find_sign(world, hero, sign)
    world.para()
    call_adult(world, adult, adult_cfg)
    reveal(world, hero, friend, place)
    educate(world, adult, lesson)
    world.para()
    ending(world, hero, friend, lesson)

    world.facts["outcome"] = "climb" if climb else "call"
    world.facts["used_climb"] = climb
    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    weather: str
    sign: str
    lesson: str
    adult: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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
    "falcon": [
        (
            "What is a falcon?",
            "A falcon is a bird of prey. It has strong wings, sharp eyes, and it can fly very fast."
        )
    ],
    "educate": [
        (
            "What does educate mean?",
            "To educate someone means to help them learn and understand something new. A good explanation can make a mystery less scary."
        )
    ],
    "nest": [
        (
            "Why do birds make nests in high places?",
            "High places can help keep eggs and chicks safer from trouble on the ground. Beams, ledges, and quiet corners can feel protected."
        )
    ],
    "feather": [
        (
            "What can a feather tell you?",
            "A feather can be a clue that a bird has been nearby. Careful clues help people figure out what is really happening."
        )
    ],
    "bird_sign": [
        (
            "Why do people look for signs when they hear an animal?",
            "Signs like feathers, nests, or droppings help show which animal was there. That is how guessing turns into knowing."
        )
    ],
    "storm": [
        (
            "Why do sounds feel scarier in a storm?",
            "Storms add thunder, wind, and flashing light, so small sounds can seem bigger and stranger. That can make people imagine something spooky."
        )
    ],
    "mist": [
        (
            "Why can mist make a place feel spooky?",
            "Mist hides edges and softens shapes, so familiar things look strange. When you cannot see clearly, your imagination works harder."
        )
    ],
    "wind": [
        (
            "Why does wind make odd sounds around old buildings?",
            "Wind pushes through cracks, boards, and corners, which can make whistles and taps. Those sounds can seem mysterious until you know where they come from."
        )
    ],
    "watch": [
        (
            "Why should people stay quiet near a bird nest?",
            "Quiet helps keep nesting birds calm. If people come too close or make too much noise, the birds may feel unsafe."
        )
    ],
    "book": [
        (
            "How can a field guide help?",
            "A field guide shows pictures and facts about animals and plants. It helps people match clues to the right creature."
        )
    ],
}

KNOWLEDGE_ORDER = ["falcon", "educate", "nest", "feather", "bird_sign", "storm", "mist", "wind", "watch", "book"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    weather = f["weather_cfg"]
    sign = f["sign_cfg"]
    lesson = f["lesson_cfg"]
    return [
        f'Write a gentle ghost-story suspense tale for ages 3 to 5 where children hear a spooky cry in an {place.label} and later learn it came from a falcon.',
        f'Write a child-facing mystery story that includes the words "falcon" and "educate", with {weather.id} weather, a ghostly misunderstanding, and a warm explanation.',
        f"Tell a suspenseful but safe story where a strange clue like a {sign.label} helps turn fear into learning, ending with {lesson.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    place = f["place_cfg"]
    weather = f["weather_cfg"]
    sign = f["sign_cfg"]
    lesson = f["lesson_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two children who heard a frightening sound near the {place.label}. It is also about the {adult.label_word} who helped them understand what was really there."
        ),
        (
            "Why did the children think there might be a ghost?",
            f"They heard a thin cry coming from {place.dark_spot}, and the old building threw the sound back in a strange way. Because the night was {weather.id}, the dark and the echoes made an ordinary animal sound feel spooky."
        ),
        (
            f"What clue did the children find?",
            f"They found {sign.label}. That clue mattered because it fit a real bird much better than a ghost."
        ),
        (
            "What was really making the scary sound?",
            "A falcon near its nest was making the cry. The children were scared at first because they did not know what they were hearing."
        ),
        (
            "How did the adult help?",
            f"The {adult.label_word} brought calm light and explained what the children were seeing. Instead of laughing at them, the adult chose to educate them so fear could turn into understanding."
        ),
    ]
    if outcome == "climb":
        qa.append(
            (
                f"Did {hero.label} and {friend.label} run away?",
                f"No. They felt frightened, but curiosity helped them take careful steps closer. Finding the clue gave them a reason to keep looking until the adult arrived."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} and {friend.label} stay at the bottom instead of climbing?",
                f"The night felt too sharp and spooky to investigate alone, so they chose the safer plan and called for help. That decision kept the suspense in the story without putting them in danger."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with wonder instead of fear. After the lesson about the falcon, the old place no longer seemed haunted, and the children walked away feeling calmer and wiser."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"falcon", "educate"}
    tags |= set(world.facts["lesson_cfg"].tags)
    tags |= set(world.facts["sign_cfg"].tags)
    tags |= set(world.facts["weather_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,S) :- place(P), sign(S), supports(P,S), explains(S,P).

fear_level(W,T,F+TB) :- weather(W), trait(T), fear_boost(W,F), timid_bonus(T,TB).
can_climb(W,T) :- fear_level(W,T,L), L <= 1.
outcome(climb) :- chosen_weather(W), chosen_trait(T), can_climb(W,T).
outcome(call) :- chosen_weather(W), chosen_trait(T), not can_climb(W,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sign_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, sign_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        for place_id in sorted(sign.explains):
            lines.append(asp.fact("explains", sign_id, place_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("fear_boost", weather_id, weather.fear_boost))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
        timid = 1 if trait in {"careful", "quiet"} else 0
        if trait == "brave":
            timid = -1
        lines.append(asp.fact("timid_bonus", trait, timid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle suspense ghost-story world where eerie sounds turn out to be a falcon nest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, sign) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sign and not valid_combo(args.place, args.sign):
        raise StoryError(explain_rejection(args.place, args.sign))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sign is None or combo[1] == args.sign)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sign_id = rng.choice(sorted(combos))
    weather_id = args.weather or rng.choice(sorted(WEATHERS))
    lesson_id = args.lesson or rng.choice(sorted(LESSONS))
    adult_id = args.adult or rng.choice(sorted(ADULTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        weather=weather_id,
        sign=sign_id,
        lesson=lesson_id,
        adult=adult_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.lesson not in LESSONS:
        raise StoryError(f"(Unknown lesson: {params.lesson})")
    if params.adult not in ADULTS:
        raise StoryError(f"(Unknown adult role: {params.adult})")
    if not valid_combo(params.place, params.sign):
        raise StoryError(explain_rejection(params.place, params.sign))

    world = tell(
        place=PLACES[params.place],
        weather=WEATHERS[params.weather],
        sign=SIGNS[params.sign],
        lesson=LESSONS[params.lesson],
        adult_cfg=ADULTS[params.adult],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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


CURATED = [
    StoryParams(
        place="bell_tower",
        weather="misty",
        sign="feather",
        lesson="field_guide",
        adult="teacher",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="chapel_roof",
        weather="windy",
        sign="nest_twigs",
        lesson="quiet_watch",
        adult="caretaker",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        trait="brave",
    ),
    StoryParams(
        place="mill_loft",
        weather="stormy",
        sign="whitewash",
        lesson="nest_rule",
        adult="ranger",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        trait="careful",
    ),
]


def asp_verify() -> int:
    rc = 0
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: ASP gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        py_outcome = outcome_of(params)
        clingo_outcome = asp_outcome(params)
        if py_outcome != clingo_outcome:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sign) pairs:\n")
        for place_id, sign_id in combos:
            print(f"  {place_id:12} {sign_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} ({p.weather}, {p.sign}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
