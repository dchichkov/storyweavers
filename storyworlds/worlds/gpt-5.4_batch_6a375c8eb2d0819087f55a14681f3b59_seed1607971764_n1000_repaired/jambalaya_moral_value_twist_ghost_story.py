#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py
=====================================================================

A standalone storyworld for a tiny ghost-story domain with a moral twist.

Reference seed:
    Write a story that includes the word "jambalaya" and uses Moral Value,
    Twist, and Ghost Story style.

World premise:
    A child carries warm jambalaya on a windy night near a place people say is
    haunted. A pale, ghostly figure appears. The child can react with either
    fear or kindness, but only some "ghost sightings" are physically
    reasonable in the chosen place and weather. In the happy stories, kindness
    leads the child closer and reveals the twist: the "ghost" was not a ghost
    after all, but a lonely person or a harmless animal made spooky by wind,
    cloth, and shadow. The ending image proves the change: a frightening porch
    becomes a warm shared supper.

Reasonableness constraint:
    Not every spooky cause works everywhere. A curtain cannot billow on an open
    dock with no window; a sheet-draped person needs a sheltered porch or hall;
    glowing fireflies can look ghostly outside but not in a sealed indoor room.
    The world only generates combinations where the ghostly appearance is
    plausible and where the chosen response fits the cause.

Run it
------
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --place porch --cause quilt_figure
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --cause curtain_shadow
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/jambalaya_moral_value_twist_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    phrase: str
    shelter: bool
    indoors: bool
    has_window: bool
    waterside: bool
    creak_text: str
    ending_image: str
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
class Cause:
    id: str
    label: str
    source_kind: str            # person | curtain | fireflies | cat
    needs_shelter: bool
    needs_window: bool
    outdoors_only: bool
    indoors_only: bool
    reveal: str
    spooky_line: str
    clue: str
    kind_response_ok: set[str]
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
    approach_kind: str          # offer_bowl | speak_softly | follow_sound
    brave: int
    text: str
    kind_text: str
    works_for: set[str]
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
class Meal:
    id: str
    label: str
    smell: str
    steam: str
    share_line: str
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


def _r_spooky_shape(world: World) -> list[str]:
    place = world.place
    cause = world.facts["cause_cfg"]
    if not ghostly_possible(place, cause):
        return []
    sig = ("spooky_shape", place.id, cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("shape").meters["ghostly"] += 1
    hero = world.get("hero")
    hero.memes["fear"] += 1
    return ["__shape__"]


def _r_smell_draws(world: World) -> list[str]:
    meal = world.get("meal")
    if meal.meters["fragrant"] < THRESHOLD:
        return []
    sig = ("smell_draws",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source = world.get("source")
    if source.role == "lonely_neighbor":
        source.meters["drawn_by_smell"] += 1
        source.meters["hunger"] += 1
    if source.role == "cat":
        source.meters["drawn_by_smell"] += 1
    return []


def _r_kindness_calms(world: World) -> list[str]:
    hero = world.get("hero")
    source = world.get("source")
    if hero.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kindness_calms", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["courage"] += 1
    source.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spooky_shape", tag="physical", apply=_r_spooky_shape),
    Rule(name="smell_draws", tag="physical", apply=_r_smell_draws),
    Rule(name="kindness_calms", tag="social", apply=_r_kindness_calms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def ghostly_possible(place: Place, cause: Cause) -> bool:
    if cause.needs_shelter and not place.shelter:
        return False
    if cause.needs_window and not place.has_window:
        return False
    if cause.outdoors_only and place.indoors:
        return False
    if cause.indoors_only and not place.indoors:
        return False
    return True


def response_fits(cause: Cause, response: Response) -> bool:
    return response.id in cause.kind_response_ok and cause.id in response.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            if not ghostly_possible(place, cause):
                continue
            for response_id, response in RESPONSES.items():
                if response_fits(cause, response):
                    combos.append((place_id, cause_id, response_id))
    return combos


def explain_rejection(place: Place, cause: Cause) -> str:
    if cause.needs_window and not place.has_window:
        return (f"(No story: {cause.label} needs a window to throw a ghostly shape, "
                f"but {place.label} has no window for that effect.)")
    if cause.needs_shelter and not place.shelter:
        return (f"(No story: {cause.label} needs a sheltered place to hang or hide, "
                f"but {place.label} is too open and windy.)")
    if cause.outdoors_only and place.indoors:
        return (f"(No story: {cause.label} works outdoors, but {place.label} is indoors.)")
    if cause.indoors_only and not place.indoors:
        return (f"(No story: {cause.label} works indoors, but {place.label} is outside.)")
    return "(No story: this spooky cause does not fit this place.)"


def explain_response(cause: Cause, response: Response) -> str:
    return (f"(No story: response '{response.id}' does not fit {cause.label}. "
            f"Try one of: {', '.join(sorted(cause.kind_response_ok))}.)")


def predict_reveal(place: Place, cause: Cause, response: Response) -> dict:
    if not ghostly_possible(place, cause):
        return {"ghostly": False, "revealed": False}
    return {
        "ghostly": True,
        "revealed": response_fits(cause, response),
    }


def introduce(world: World, hero: Entity, parent: Entity, meal: Meal) -> None:
    hero.memes["love"] += 1
    world.get("meal").meters["fragrant"] = 1.0
    world.say(
        f"On a windy evening, {hero.id} followed {parent.label_word}'s careful steps "
        f"with a warm pot of {meal.label}. {meal.steam} and {meal.smell}."
    )
    world.say(
        f"{hero.id} liked the brave feeling of carrying supper, even while the dark "
        f"made every corner seem deeper than daytime."
    )


def arrive(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"They came to {place.phrase}. {place.creak_text}"
    )


def seed_spook(world: World, cause: Cause) -> None:
    propagate(world, narrate=False)
    shape = world.get("shape")
    if shape.meters["ghostly"] >= THRESHOLD:
        world.say(cause.spooky_line)
        world.say("At once, the night seemed full of old stories about ghosts.")
    else:
        world.say("The place was dark, but nothing there could truly look ghostly.")


def react(world: World, hero: Entity, response: Response) -> None:
    hero.memes["courage"] += float(response.brave) / 2.0
    hero.memes["kindness"] += 1.0
    propagate(world, narrate=False)
    world.say(response.text)


def reveal(world: World, hero: Entity, source: Entity, cause: Cause, response: Response,
           meal: Meal, parent: Entity, place: Place) -> None:
    source.meters["revealed"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    source.memes["gratitude"] += 1
    world.say(cause.reveal)
    if source.role == "lonely_neighbor":
        world.say(
            f"It was only {source.label}, wrapped in pale cloth against the wind and "
            f"drawn close by the smell of supper. {parent.label_word.capitalize()} "
            f"recognized {source.pronoun('object')} at once."
        )
        world.say(
            f'"I thought I was seeing a ghost," {hero.id} whispered. '
            f'"No," said {parent.label_word}, smiling softly. "Just a lonely neighbor."'
        )
        world.say(
            f"{hero.id} remembered the warm pot in {hero.pronoun('possessive')} hands and "
            f"{meal.share_line}"
        )
    elif source.role == "cat":
        world.say(
            f"It was only {source.label}, a skinny cat with moon-bright eyes and a torn white sack "
            f"caught over {source.pronoun('possessive')} back. The sack had fluttered like a ghost in the dark."
        )
        world.say(
            f"{hero.id} let out a shaky laugh. The scariest shape in the night had been a hungry little cat all along."
        )
        world.say(
            f"{parent.label_word.capitalize()} set a small safe spoonful of rice beside the steps and kept the rest of the {meal.label} warm for home."
        )
    world.say(
        f"After that, {place.ending_image}"
    )


def moral_close(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} learned that fear can make shadows taller than they are, "
        f"but a kind heart can bring the truth close enough to see."
    )


def tell(place: Place, cause: Cause, response: Response, meal: Meal,
         hero_name: str = "Lena", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["curious", "gentle"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    meal_ent = world.add(Entity(
        id="meal",
        kind="thing",
        type="food",
        label=meal.label,
        role="meal",
        attrs={},
    ))
    shape = world.add(Entity(
        id="shape",
        kind="thing",
        type="shape",
        label="the pale shape",
        role="spooky_shape",
        attrs={},
    ))

    if cause.source_kind == "person":
        source = world.add(Entity(
            id="source",
            kind="character",
            type="man",
            label="Mr. Batiste",
            role="lonely_neighbor",
            attrs={"wrapped": "old white quilt"},
        ))
    elif cause.source_kind == "cat":
        source = world.add(Entity(
            id="source",
            kind="thing",
            type="cat",
            label="a skinny stray cat",
            role="cat",
            attrs={"wrapped": "torn white sack"},
        ))
    else:
        source = world.add(Entity(
            id="source",
            kind="thing",
            type="thing",
            label="the harmless cause",
            role="lonely_neighbor" if cause.source_kind == "curtain" else "cat",
            attrs={},
        ))
        if cause.source_kind == "curtain":
            source.kind = "character"
            source.type = "woman"
            source.label = "Miss Odette"
            source.attrs["wrapped"] = "a pale lace curtain"
        elif cause.source_kind == "fireflies":
            source.label = "a drift of fireflies"
            source.role = "cat"

    for ent in (hero, parent, meal_ent, shape, source):
        ent.meters["revealed"] = ent.meters.get("revealed", 0.0)
        ent.meters["hunger"] = ent.meters.get("hunger", 0.0)
        ent.meters["drawn_by_smell"] = ent.meters.get("drawn_by_smell", 0.0)
        ent.memes["fear"] = ent.memes.get("fear", 0.0)
        ent.memes["trust"] = ent.memes.get("trust", 0.0)
        ent.memes["gratitude"] = ent.memes.get("gratitude", 0.0)
        ent.memes["kindness"] = ent.memes.get("kindness", 0.0)
        ent.memes["courage"] = ent.memes.get("courage", 0.0)
        ent.memes["relief"] = ent.memes.get("relief", 0.0)
        ent.memes["wisdom"] = ent.memes.get("wisdom", 0.0)

    world.facts.update(
        place_cfg=place,
        cause_cfg=cause,
        response_cfg=response,
        meal_cfg=meal,
        hero=hero,
        parent=parent,
        source=source,
        shape=shape,
    )

    propagate(world, narrate=False)

    introduce(world, hero, parent, meal)
    arrive(world, hero, place)

    world.para()
    seed_spook(world, cause)
    world.say(cause.clue)

    world.para()
    react(world, hero, response)
    reveal(world, hero, source, cause, response, meal, parent, place)
    moral_close(world, hero)

    world.facts.update(
        revealed=source.meters["revealed"] >= THRESHOLD,
        kind=hero.memes["kindness"] >= THRESHOLD,
        fear_started=world.get("shape").meters["ghostly"] >= THRESHOLD,
        twist_true=True,
    )
    return world


PLACES = {
    "porch": Place(
        id="porch",
        label="the old porch",
        phrase="the old porch of a peeling bayou house",
        shelter=True,
        indoors=False,
        has_window=True,
        waterside=False,
        creak_text="The boards gave a long, complaining creak, and the porch roof knocked softly above them.",
        ending_image="the porch no longer looked haunted at all; it looked like a place where supper and stories could be shared.",
        tags={"porch", "house"},
    ),
    "hall": Place(
        id="hall",
        label="the parish hall",
        phrase="the dim parish hall at the edge of town",
        shelter=True,
        indoors=True,
        has_window=True,
        waterside=False,
        creak_text="Its high windows rattled, and every little sound echoed as if someone had answered from far away.",
        ending_image="the hall felt less like a haunted box of echoes and more like a safe room glowing around warm food.",
        tags={"hall", "window"},
    ),
    "dock": Place(
        id="dock",
        label="the old dock",
        phrase="the old dock stretching out over black water",
        shelter=False,
        indoors=False,
        has_window=False,
        waterside=True,
        creak_text="Water slapped the posts below, and the dock planks clicked under each careful step.",
        ending_image="the dark dock seemed smaller now, with the moon on the water and no ghost in sight.",
        tags={"dock", "water"},
    ),
}

CAUSES = {
    "quilt_figure": Cause(
        id="quilt_figure",
        label="a quilt-wrapped figure",
        source_kind="person",
        needs_shelter=True,
        needs_window=False,
        outdoors_only=False,
        indoors_only=False,
        reveal="The white shape shifted, and instead of floating away, it gave a small cough and lowered an old quilt from a human face.",
        spooky_line="Near the far post stood a tall white figure, still as a grave marker and pale in the swinging light.",
        clue="The shape did not moan or rattle chains. It only leaned toward the smell of the jambalaya, as if supper mattered more than haunting.",
        kind_response_ok={"offer_bowl", "speak_softly"},
        tags={"person", "quilt"},
    ),
    "curtain_shadow": Cause(
        id="curtain_shadow",
        label="a curtain-shaped shadow",
        source_kind="curtain",
        needs_shelter=True,
        needs_window=True,
        outdoors_only=False,
        indoors_only=False,
        reveal="A gust lifted the pale curtain, and behind it stood Miss Odette, trying to untangle the cloth from the latch with chilly fingers.",
        spooky_line="A white face seemed to bloom in the window, then drift sideways as if it had no feet at all.",
        clue="Then came a sharp little mutter that sounded much more annoyed than ghostly.",
        kind_response_ok={"speak_softly", "follow_sound"},
        tags={"window", "curtain"},
    ),
    "firefly_swirl": Cause(
        id="firefly_swirl",
        label="a swirl of fireflies",
        source_kind="fireflies",
        needs_shelter=False,
        needs_window=False,
        outdoors_only=True,
        indoors_only=False,
        reveal="The floating lights broke apart, and what had looked like a face became only fireflies wheeling around something low and thin by the ground.",
        spooky_line="Out in the dark, a pale blur with blinking eyes seemed to hover above the boards.",
        clue="The blinking did not stay in two eyes the way a real face would. It scattered and gathered again.",
        kind_response_ok={"follow_sound"},
        tags={"outdoors", "fireflies"},
    ),
    "sack_cat": Cause(
        id="sack_cat",
        label="a sack-draped cat",
        source_kind="cat",
        needs_shelter=False,
        needs_window=False,
        outdoors_only=False,
        indoors_only=False,
        reveal="There came a tiny meow, and the pale thing stumbled forward on four paws instead of floating on none.",
        spooky_line="Something small and white slid along the edge of the dark, silent enough to make the hair on {hero}'s neck prickle.",
        clue="It stopped once to sniff the air and gave the faintest hungry rustle.",
        kind_response_ok={"offer_bowl", "follow_sound"},
        tags={"cat", "animal"},
    ),
}

RESPONSES = {
    "offer_bowl": Response(
        id="offer_bowl",
        approach_kind="offer_bowl",
        brave=2,
        text='Instead of running, the child lifted the pot a little and said, "If you are hungry, we can share."',
        kind_text="offered to share the food instead of running away",
        works_for={"quilt_figure", "sack_cat"},
        tags={"share", "kindness"},
    ),
    "speak_softly": Response(
        id="speak_softly",
        approach_kind="speak_softly",
        brave=1,
        text='The child took one slow breath and called out in a soft voice, "Who is there?"',
        kind_text="spoke gently to the frightening shape",
        works_for={"quilt_figure", "curtain_shadow"},
        tags={"gentle", "kindness"},
    ),
    "follow_sound": Response(
        id="follow_sound",
        approach_kind="follow_sound",
        brave=2,
        text="The child listened for the truest little sound in the dark and stepped toward it, one careful foot at a time.",
        kind_text="followed the real sound instead of the scary shape",
        works_for={"curtain_shadow", "firefly_swirl", "sack_cat"},
        tags={"observe", "bravery"},
    ),
}

MEALS = {
    "jambalaya": Meal(
        id="jambalaya",
        label="jambalaya",
        smell="the spicy smell of rice, onions, and sausage drifted ahead of them",
        steam="Steam curled from under the lid",
        share_line="offered a warm bowl before fear could climb back into the room",
        tags={"jambalaya", "food"},
    ),
}

GIRL_NAMES = ["Lena", "Mira", "Tess", "Nina", "Ada", "June", "Cora", "Lila"]
BOY_NAMES = ["Jonah", "Eli", "Beau", "Micah", "Theo", "Noel", "Reed", "Silas"]


@dataclass
class StoryParams:
    place: str
    cause: str
    response: str
    meal: str = "jambalaya"
    name: str = "Lena"
    gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    cause = f["cause_cfg"]
    response = f["response_cfg"]
    meal = f["meal_cfg"]
    return [
        f'Write a short ghost story for a 3-to-5-year-old that includes the word "{meal.label}" and ends with a gentle twist.',
        f"Tell a spooky-but-safe story where a {hero.type} named {hero.id} sees {cause.label} at {place.label} and chooses kindness instead of panic.",
        f"Write a moral ghost story in which a child {response.kind_text}, discovers the scary thing is harmless, and learns that fear can be wrong.",
    ]


KNOWLEDGE = {
    "jambalaya": [(
        "What is jambalaya?",
        "Jambalaya is a rice dish cooked with seasonings and often vegetables and meat. It smells strong and warm, so people notice it quickly."
    )],
    "ghost": [(
        "Why can something look like a ghost in the dark?",
        "In the dark, wind, cloth, shadows, and little lights can make ordinary things look strange. Your eyes see only part of the picture until you get closer."
    )],
    "kindness": [(
        "Why is kindness helpful when someone seems scary but might need help?",
        "Kindness can slow you down enough to see what is really happening. Sometimes a gentle voice or a small offer turns fear into understanding."
    )],
    "cat": [(
        "Why might a hungry cat come near warm food?",
        "A hungry cat follows smell. Warm food carries a strong scent, so the cat may sneak close even if it is frightened."
    )],
    "fireflies": [(
        "What are fireflies?",
        "Fireflies are small insects that blink with light. At night, many of them together can look mysterious from far away."
    )],
    "curtain": [(
        "Why does a curtain look spooky in the wind?",
        "A curtain can billow, twist, and catch the light. When it moves suddenly, it may look like a floating person for a moment."
    )],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    source = f["source"]
    place = f["place_cfg"]
    cause = f["cause_cfg"]
    response = f["response_cfg"]
    meal = f["meal_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {hero.pronoun('possessive')} {parent.label_word} carrying {meal.label} to {place.label}. They walk into a dark, creaky place where something looks like a ghost."
        ),
        (
            f"What made the place feel spooky?",
            f"{place.creak_text} Then {cause.spooky_line.replace('{hero}', hero.id)} The strange shape and the night sounds worked together to make the child afraid."
        ),
        (
            f"Why did the child not run away right away?",
            f"{hero.id} chose kindness and courage instead of panic. {response.text} That choice brought the truth closer instead of letting fear grow bigger."
        ),
    ]
    if source.role == "lonely_neighbor":
        qa.append((
            "What was the twist at the end?",
            f"The ghost was not a ghost at all. It was {source.label}, and the pale shape came from cloth, shadow, and darkness. The twist matters because the scary mystery turns into a chance to help someone."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{hero.id} learned that fear can fool you when you only see a shape in the dark. Kindness helped {hero.pronoun('object')} discover a lonely person and share supper instead of hiding."
        ))
    else:
        qa.append((
            "What was the twist at the end?",
            f"The ghostly shape turned out to be {source.label}. It looked frightening only because the dark changed the way it seemed from far away."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{hero.id} learned that not every frightening thing is dangerous. Looking carefully and acting gently helped {hero.pronoun('object')} see the truth."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cause = f["cause_cfg"]
    tags = {"jambalaya", "ghost", "kindness"} | set(cause.tags)
    out: list[tuple[str, str]] = []
    order = ["jambalaya", "ghost", "kindness", "cat", "fireflies", "curtain"]
    for tag in order:
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="porch",
        cause="quilt_figure",
        response="offer_bowl",
        meal="jambalaya",
        name="Lena",
        gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="hall",
        cause="curtain_shadow",
        response="speak_softly",
        meal="jambalaya",
        name="Jonah",
        gender="boy",
        parent="father",
    ),
    StoryParams(
        place="dock",
        cause="firefly_swirl",
        response="follow_sound",
        meal="jambalaya",
        name="Mira",
        gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="porch",
        cause="sack_cat",
        response="offer_bowl",
        meal="jambalaya",
        name="Beau",
        gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
% Reasonableness of spooky cause in a place.
ghostly_possible(P, C) :- place(P), cause(C),
                          not needs_shelter(C).
ghostly_possible(P, C) :- place(P), cause(C),
                          needs_shelter(C), shelter(P).
:- ghostly_possible(P, C), needs_window(C), not has_window(P).
:- ghostly_possible(P, C), outdoors_only(C), indoors(P).
:- ghostly_possible(P, C), indoors_only(C), not indoors(P).

valid_place_cause(P, C) :- place(P), cause(C), ghostly_possible(P, C).

% Response fit.
fits(C, R) :- response_ok(C, R), response_works(R, C).

valid(P, C, R) :- valid_place_cause(P, C), fits(C, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.shelter:
            lines.append(asp.fact("shelter", place_id))
        if place.indoors:
            lines.append(asp.fact("indoors", place_id))
        if place.has_window:
            lines.append(asp.fact("has_window", place_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        if cause.needs_shelter:
            lines.append(asp.fact("needs_shelter", cause_id))
        if cause.needs_window:
            lines.append(asp.fact("needs_window", cause_id))
        if cause.outdoors_only:
            lines.append(asp.fact("outdoors_only", cause_id))
        if cause.indoors_only:
            lines.append(asp.fact("indoors_only", cause_id))
        for rid in sorted(cause.kind_response_ok):
            lines.append(asp.fact("response_ok", cause_id, rid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        for cid in sorted(response.works_for):
            lines.append(asp.fact("response_works", rid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolve/generate produced empty story")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a ghostly misunderstanding, and a kind twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--meal", choices=MEALS, default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos() and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not ghostly_possible(place, cause):
            raise StoryError(explain_rejection(place, cause))
    if args.cause and args.response:
        cause = CAUSES[args.cause]
        response = RESPONSES[args.response]
        if not response_fits(cause, response):
            raise StoryError(explain_response(cause, response))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.cause is None or c[1] == args.cause)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    meal = args.meal or "jambalaya"
    return StoryParams(
        place=place_id,
        cause=cause_id,
        response=response_id,
        meal=meal,
        name=name,
        gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal: {params.meal})")

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]
    if not ghostly_possible(place, cause):
        raise StoryError(explain_rejection(place, cause))
    if not response_fits(cause, response):
        raise StoryError(explain_response(cause, response))

    world = tell(
        place=place,
        cause=cause,
        response=response,
        meal=MEALS[params.meal],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, response) combos:\n")
        for place, cause, response in combos:
            print(f"  {place:8} {cause:15} {response}")
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
            header = f"### {p.name}: {p.cause} at {p.place} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
