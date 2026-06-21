#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py
=====================================================================

A standalone storyworld about a child, a nervous goose, and a tiny neighborhood
parade. The child wants to carry a card with a warm adjective on it, but the
adjective must be honest: the goose has to grow into it during the story.

The world model keeps track of a few simple physical meters and emotional memes:
fear leads to a honk, a woven comfort item settles the goose, and the ending
image proves why the chosen adjective was true all along.

Run it
------
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py --place garden_path --obstacle bridge --comfort willow_basket --adjective brave
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py --obstacle bridge --adjective funny
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/honk_adjective_weave_humor_heartwarming.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    affords: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    sight: str
    worry: str
    needs: set[str] = field(default_factory=set)
    outcome: str = ""
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
class Comfort:
    id: str
    label: str
    phrase: str
    weave_text: str
    supports: set[str] = field(default_factory=set)
    settle_text: str = ""
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
class AdjectiveCard:
    id: str
    word: str
    ending: str
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


def _r_honk(world: World) -> list[str]:
    goose = world.entities.get("goose")
    if goose is None:
        return []
    if goose.memes["fear"] < THRESHOLD:
        return []
    sig = ("honk", int(goose.meters["honks"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goose.meters["honks"] += 1
    return ["__honk__"]


def _r_ready_proud(world: World) -> list[str]:
    goose = world.entities.get("goose")
    card = world.entities.get("card")
    comfort = world.entities.get("comfort_item")
    if goose is None or card is None or comfort is None:
        return []
    if comfort.meters["woven"] < THRESHOLD:
        return []
    if card.meters["hung"] < THRESHOLD:
        return []
    sig = ("ready_proud",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goose.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="honk", tag="social", apply=_r_honk),
    Rule(name="ready_proud", tag="emotional", apply=_r_ready_proud),
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
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


def comfort_works(obstacle: Obstacle, comfort: Comfort) -> bool:
    return bool(obstacle.needs & comfort.supports)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            obstacle = OBSTACLES[obstacle_id]
            for comfort_id, comfort in COMFORTS.items():
                if not comfort_works(obstacle, comfort):
                    continue
                for adjective_id, adjective in ADJECTIVES.items():
                    if adjective.ending == obstacle.outcome:
                        combos.append((place_id, obstacle_id, comfort_id, adjective_id))
    return combos


def explain_comfort(obstacle: Obstacle, comfort: Comfort) -> str:
    need = " or ".join(sorted(obstacle.needs))
    have = " or ".join(sorted(comfort.supports))
    return (
        f"(No story: {comfort.label} cannot honestly help with {obstacle.label}. "
        f"The obstacle needs {need}, but {comfort.label} only offers {have}.)"
    )


def explain_adjective(obstacle: Obstacle, adjective: AdjectiveCard) -> str:
    return (
        f'(No story: the ending at {obstacle.label} proves the goose was '
        f'"{ADJECTIVES[obstacle.outcome].word}", not "{adjective.word}". '
        f'The adjective card has to match what really happens.)'
    )


def outcome_of(params: "StoryParams") -> str:
    return OBSTACLES[params.obstacle].outcome


def predict_honk(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    goose = sim.get("goose")
    goose.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "will_honk": goose.meters["honks"] >= THRESHOLD,
        "fear": goose.memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, goose: Entity, adjective: AdjectiveCard) -> None:
    world.say(
        f"{child.id} and {helper.label} were getting ready for the tiny parade at "
        f"{world.place.label}. {world.place.intro}"
    )
    world.say(
        f"Their goose, {goose.id}, waddled beside them with round feet and a very serious face."
    )
    world.say(
        f'{child.id} held up a little card that said "{adjective.word}." '
        f'"If we hang this on your wagon," {child.pronoun()} said, "we have to earn it."'
    )


def set_goal(world: World, child: Entity, goose: Entity) -> None:
    child.memes["hope"] += 1
    goose.memes["trust"] += 1
    world.say(
        f"{child.id} wanted {goose.id} to roll through the parade without any scared flapping. "
        f"That seemed simple until they reached the middle of the path."
    )


def spot_obstacle(world: World, child: Entity, helper: Entity, goose: Entity, obstacle: Obstacle) -> None:
    goose.memes["fear"] += 1
    world.say(
        f"There, right ahead of them, was {obstacle.sight}. {obstacle.worry}"
    )
    pred = predict_honk(world, obstacle)
    world.facts["predicted_honk"] = pred["will_honk"]
    world.facts["predicted_fear"] = pred["fear"]
    propagate(world, narrate=False)
    if goose.meters["honks"] >= THRESHOLD:
        world.say(
            f'{goose.id} stretched {goose.pronoun("possessive")} neck and gave one loud honk that made '
            f"{helper.label} blink and {child.id} laugh even while {child.pronoun()} jumped."
        )


def decide_to_weave(world: World, child: Entity, helper: Entity, comfort: Comfort) -> None:
    child.memes["resolve"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"Let\'s not rush {goose.id}," {helper.label} said. '
        f'"We can weave {comfort.phrase} first."'
    )


def weave_comfort(world: World, child: Entity, helper: Entity, comfort_ent: Entity, comfort: Comfort) -> None:
    comfort_ent.meters["woven"] += 1
    child.memes["focus"] += 1
    goose = world.get("goose")
    world.say(
        f"{child.id} and {helper.label} sat on the grass and {comfort.weave_text}. "
        f"{goose.id} watched every loop as if it were the most important sewing in town."
    )


def settle_goose(world: World, child: Entity, goose: Entity, comfort_ent: Entity, comfort: Comfort) -> None:
    goose.memes["fear"] = 0.0
    goose.memes["trust"] += 1
    goose.memes["relief"] += 1
    comfort_ent.meters["used"] += 1
    world.say(comfort.settle_text)


def hang_card(world: World, card: Entity, adjective: AdjectiveCard) -> None:
    card.meters["hung"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{world.get("goose").id} let {child_safe(world).pronoun("object")} tie on the "{adjective.word}" card without another fuss.'
    )


def child_safe(world: World) -> Entity:
    return world.get("child")


def ending_for(world: World, child: Entity, helper: Entity, goose: Entity, obstacle: Obstacle, adjective: AdjectiveCard) -> None:
    goose.memes["joy"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    if obstacle.outcome == "brave":
        goose.meters["crossed"] += 1
        world.say(
            f"When the little bridge creaked, {goose.id} paused, tucked {goose.pronoun('possessive')} feet, "
            f"and then rode across as steady as a drumbeat."
        )
        world.say(
            f'"Brave fits now," {child.id} whispered. {helper.label} nodded, and the wagon rolled on under strings of paper flags.'
        )
    elif obstacle.outcome == "gentle":
        goose.meters["nuzzle"] += 1
        world.say(
            f"{goose.id} peeped out from the soft cover, saw the laundry flutter again, and stayed calm."
        )
        world.say(
            f"Then {goose.pronoun().capitalize()} leaned over and brushed {child.id}'s cheek with a warm beak so softly that "
            f'{child.pronoun()} giggled. "Gentle fits now," {helper.label} said.'
        )
    else:
        goose.meters["bow"] += 1
        world.say(
            f"{goose.id} noticed {goose.pronoun('possessive')} face in the bright cart, gave one surprised honk, "
            f"and then bowed to the reflection as if greeting another goose mayor."
        )
        world.say(
            f"The people by the path laughed kindly, and even {child.id} had to hold {child.pronoun('possessive')} tummy. "
            f'"Funny fits now," {helper.label} said.'
        )
    world.say(
        f"By the time they reached the parade circle, the card fluttered in the breeze and everybody could see it was true."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    comfort: Comfort,
    adjective: AdjectiveCard,
    *,
    child_name: str = "Lena",
    child_gender: str = "girl",
    goose_name: str = "Muffin",
    helper_type: str = "grandpa",
) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=("Grandpa" if helper_type == "grandpa" else "Aunt May"), role="helper"))
    goose = world.add(Entity(id="goose", kind="character", type="goose", label=goose_name, role="goose"))
    card = world.add(Entity(id="card", kind="thing", type="card", label=adjective.word, role="card"))
    comfort_ent = world.add(Entity(id="comfort_item", kind="thing", type="comfort", label=comfort.label, role="comfort"))

    child.attrs["name"] = child_name
    helper.attrs["name"] = helper.label
    goose.attrs["name"] = goose_name
    world.facts["child_name"] = child_name
    world.facts["goose_name"] = goose_name

    introduce(world, child_named(child), helper, goose_named(goose), adjective)
    set_goal(world, child_named(child), goose_named(goose))

    world.para()
    spot_obstacle(world, child_named(child), helper, goose_named(goose), obstacle)
    decide_to_weave(world, child_named(child), helper, comfort)
    weave_comfort(world, child_named(child), helper, comfort_ent, comfort)
    settle_goose(world, child_named(child), goose_named(goose), comfort_ent, comfort)
    hang_card(world, card, adjective)

    world.para()
    ending_for(world, child_named(child), helper, goose_named(goose), obstacle, adjective)

    world.facts.update(
        place=place,
        obstacle=obstacle,
        comfort=comfort,
        adjective=adjective,
        child=child_named(child),
        helper=helper,
        goose=goose_named(goose),
        card=card,
        comfort_item=comfort_ent,
        honked=goose.meters["honks"] >= THRESHOLD,
        woven=comfort_ent.meters["woven"] >= THRESHOLD,
        outcome=obstacle.outcome,
    )
    return world


def child_named(ent: Entity) -> Entity:
    shown = copy.copy(ent)
    shown.id = ent.attrs.get("name", ent.label or ent.id)
    return shown


def goose_named(ent: Entity) -> Entity:
    shown = copy.copy(ent)
    shown.id = ent.attrs.get("name", ent.label or ent.id)
    return shown


PLACES = {
    "garden_path": Place(
        id="garden_path",
        label="the garden path",
        intro="Pots of mint and marigolds stood in a tidy row, and somebody had already tied yellow ribbons to the fence.",
        affords={"bridge", "laundry"},
        tags={"garden"},
    ),
    "town_green": Place(
        id="town_green",
        label="the town green",
        intro="Folded chairs waited under the trees, and a chalk circle on the ground showed where the little parade would turn.",
        affords={"bridge", "mirror_cart"},
        tags={"park"},
    ),
    "bakery_lane": Place(
        id="bakery_lane",
        label="bakery lane",
        intro="Warm bread smells floated through the air, and the baker had set tiny paper flags in the window boxes.",
        affords={"laundry", "mirror_cart"},
        tags={"street"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="the little bridge",
        sight="a little wooden bridge over a trickling stream",
        worry="The boards were safe, but they gave a soft clack-clack sound, and that was enough to make a goose think serious thoughts.",
        needs={"steady_nest"},
        outcome="brave",
        tags={"bridge"},
    ),
    "laundry": Obstacle(
        id="laundry",
        label="the fluttering laundry",
        sight="a clothesline full of fluttering sheets",
        worry="Each white sheet puffed like a sleepy ghost, which was funny to everyone except the goose.",
        needs={"soft_wrap", "shade"},
        outcome="gentle",
        tags={"laundry"},
    ),
    "mirror_cart": Obstacle(
        id="mirror_cart",
        label="the shiny cart",
        sight="a bright delivery cart with a mirror-bright side",
        worry="The side of the cart flashed back a second goose face, and sudden goose faces are not always welcome.",
        needs={"distraction", "soft_wrap"},
        outcome="funny",
        tags={"mirror"},
    ),
}

COMFORTS = {
    "ribbon_mat": Comfort(
        id="ribbon_mat",
        label="ribbon mat",
        phrase="a flat ribbon mat for the wagon floor",
        weave_text="wove bright strips of ribbon over and under until a springy little mat appeared",
        supports={"steady_nest"},
        settle_text="When they set the mat in the wagon, the goose tested it with one foot, then the other, and gave a much smaller, more thoughtful sound.",
        tags={"ribbon"},
    ),
    "willow_basket": Comfort(
        id="willow_basket",
        label="willow basket",
        phrase="a round willow basket with a low cozy rim",
        weave_text="wove bendy willow loops together until the basket looked snug enough for a royal loaf of bread",
        supports={"steady_nest", "shade"},
        settle_text="The goose tucked down inside the basket's cozy rim and blinked as if the whole world had suddenly become more sensible.",
        tags={"basket"},
    ),
    "yarn_hood": Comfort(
        id="yarn_hood",
        label="yarn hood",
        phrase="a soft yarn hood with floppy ties",
        weave_text="wove thick yarn through a little frame and made a soft hood that sat light around the goose's head",
        supports={"soft_wrap"},
        settle_text="The hood muffled the fuss around them, and the goose's feathers slowly un-ruffled one by one.",
        tags={"yarn"},
    ),
    "streamer_ring": Comfort(
        id="streamer_ring",
        label="streamer ring",
        phrase="a ring of streamers that danced in front of the wagon",
        weave_text="wove shiny streamers around a light ring until every breeze made it twirl",
        supports={"distraction"},
        settle_text="The goose followed the dancing streamers with bright eyes and forgot to worry about the path for a little while.",
        tags={"streamers"},
    ),
}

ADJECTIVES = {
    "brave": AdjectiveCard(
        id="brave",
        word="brave",
        ending="brave",
        tags={"adjective"},
    ),
    "gentle": AdjectiveCard(
        id="gentle",
        word="gentle",
        ending="gentle",
        tags={"adjective"},
    ),
    "funny": AdjectiveCard(
        id="funny",
        word="funny",
        ending="funny",
        tags={"adjective"},
    ),
}

GIRL_NAMES = ["Lena", "Mia", "Nora", "Ruby", "Tess", "Ella", "June", "Molly"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Max", "Theo", "Eli", "Sam", "Ben"]
GOOSE_NAMES = ["Muffin", "Pepper", "Noodle", "Puddle", "Buttons", "Sunny"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    comfort: str
    adjective: str
    child_name: str
    child_gender: str
    goose_name: str
    helper: str
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
    "adjective": [
        (
            "What is an adjective?",
            "An adjective is a describing word. It tells you something about a person, animal, or thing, like brave, gentle, or funny.",
        )
    ],
    "goose": [
        (
            "Why do geese honk?",
            "Geese honk to talk to each other or to warn that they feel excited or worried. A honk can sound funny, but it also tells you how the goose feels.",
        )
    ],
    "weave": [
        (
            "What does weave mean?",
            "To weave means to put strips or threads over and under each other to make something new. People can weave baskets, mats, and other soft or bendy things.",
        )
    ],
    "bridge": [
        (
            "Why might a little bridge make an animal nervous?",
            "A bridge can sound and feel different under tiny feet. New sounds and wobbly feelings can make an animal stop and think.",
        )
    ],
    "laundry": [
        (
            "Why can fluttering laundry look scary to an animal?",
            "Big sheets can flap and puff in the wind in sudden ways. To a small animal, that can feel surprising even when it is harmless.",
        )
    ],
    "mirror": [
        (
            "Why might an animal stare at a reflection?",
            "A reflection can look like another animal is suddenly there. If the animal does not know it is a mirror, that can be confusing and silly.",
        )
    ],
    "basket": [
        (
            "Why can a basket feel safe?",
            "A basket has sides that hold you in one place, so it can feel snug and steady. That can help a nervous animal relax.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon mat for?",
            "A ribbon mat makes the floor of a wagon feel softer and less slippery. A steadier place to stand can help a small animal feel brave.",
        )
    ],
    "yarn": [
        (
            "How can a soft hood help with worry?",
            "Something soft around your head can block a little noise and wind. That can make the world feel calmer and easier to handle.",
        )
    ],
    "streamers": [
        (
            "Why do moving streamers grab attention?",
            "Bright streamers dance and twirl where your eyes can follow them. Watching them can distract you from something that felt scary before.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "adjective",
    "goose",
    "weave",
    "bridge",
    "laundry",
    "mirror",
    "basket",
    "ribbon",
    "yarn",
    "streamers",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goose = f["goose"]
    adjective = f["adjective"]
    obstacle = f["obstacle"]
    comfort = f["comfort"]
    return [
        f'Write a heartwarming funny story for a 3-to-5-year-old that includes the words "honk", "adjective", and "weave".',
        f"Tell a story where {child.id} helps a goose named {goose.id} through {obstacle.label} by learning that an adjective should be true, not just pretty.",
        f"Write a gentle neighborhood parade story where a child and a helper weave {comfort.phrase} and earn the word {adjective.word} by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goose = f["goose"]
    obstacle = f["obstacle"]
    comfort = f["comfort"]
    adjective = f["adjective"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.label}, and a goose named {goose.id}. They were getting ready for a tiny parade together.",
        ),
        (
            "What was on the little card?",
            f'The card said "{adjective.word}." {child.id} wanted the adjective to be honest, not just fancy-looking.',
        ),
        (
            f"Why did {goose.id} honk?",
            f"{goose.id} honked because {obstacle.label} made {goose.pronoun('object')} nervous. The world changed in a sudden or wobbly way, and the honk showed that fear out loud.",
        ),
        (
            "How did they help the goose?",
            f"They stopped and wove {comfort.phrase}. That comfort matched the problem at {obstacle.label}, so it helped {goose.id} settle instead of panic.",
        ),
    ]
    if f["outcome"] == "brave":
        qa.append(
            (
                f"Why was the adjective {adjective.word} true at the end?",
                f'It was true because {goose.id} crossed the little bridge after feeling scared. {goose.pronoun().capitalize()} did not stop being nervous first; {goose.pronoun()} was brave by going on anyway.',
            )
        )
    elif f["outcome"] == "gentle":
        qa.append(
            (
                f"Why was the adjective {adjective.word} true at the end?",
                f'It was true because {goose.id} calmed down and brushed {child.id}\'s cheek softly with {goose.pronoun("possessive")} beak. That gentle touch showed the change better than a label alone.',
            )
        )
    else:
        qa.append(
            (
                f"Why was the adjective {adjective.word} true at the end?",
                f'It was true because {goose.id} bowed to the shiny cart after one surprised honk and made everyone laugh. The joke came from the goose treating a reflection like an important stranger.',
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"adjective", "goose", "weave"}
    tags |= set(f["obstacle"].tags)
    tags |= set(f["comfort"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden_path",
        obstacle="bridge",
        comfort="willow_basket",
        adjective="brave",
        child_name="Lena",
        child_gender="girl",
        goose_name="Muffin",
        helper="grandpa",
    ),
    StoryParams(
        place="bakery_lane",
        obstacle="laundry",
        comfort="yarn_hood",
        adjective="gentle",
        child_name="Owen",
        child_gender="boy",
        goose_name="Pepper",
        helper="aunt",
    ),
    StoryParams(
        place="town_green",
        obstacle="mirror_cart",
        comfort="streamer_ring",
        adjective="funny",
        child_name="Ruby",
        child_gender="girl",
        goose_name="Noodle",
        helper="grandpa",
    ),
    StoryParams(
        place="garden_path",
        obstacle="bridge",
        comfort="ribbon_mat",
        adjective="brave",
        child_name="Finn",
        child_gender="boy",
        goose_name="Buttons",
        helper="aunt",
    ),
    StoryParams(
        place="bakery_lane",
        obstacle="laundry",
        comfort="willow_basket",
        adjective="gentle",
        child_name="June",
        child_gender="girl",
        goose_name="Sunny",
        helper="grandpa",
    ),
]


ASP_RULES = r"""
works(O,C) :- obstacle(O), comfort(C), needs(O,N), supports(C,N).
right_word(O,A) :- obstacle(O), adjective(A), outcome(O,K), ends_as(A,K).
valid(P,O,C,A) :- place(P), affords(P,O), works(O,C), right_word(O,A).

story_outcome(O,K) :- obstacle(O), outcome(O,K), chosen_obstacle(O).
chosen_ok :- chosen_place(P), chosen_obstacle(O), chosen_comfort(C), chosen_adjective(A),
             valid(P,O,C,A).
bad_choice :- chosen_place(P), chosen_obstacle(O), chosen_comfort(C), chosen_adjective(A),
              not valid(P,O,C,A).

#show valid/4.
#show story_outcome/2.
#show chosen_ok/0.
#show bad_choice/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for oid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for need in sorted(obstacle.needs):
            lines.append(asp.fact("needs", oid, need))
        lines.append(asp.fact("outcome", oid, obstacle.outcome))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for support in sorted(comfort.supports):
            lines.append(asp.fact("supports", cid, support))
    for aid, adjective in ADJECTIVES.items():
        lines.append(asp.fact("adjective", aid))
        lines.append(asp.fact("ends_as", aid, adjective.ending))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_comfort", params.comfort),
            asp.fact("chosen_adjective", params.adjective),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "story_outcome")
    return out[0][1] if out else "?"


def asp_choice_ok(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_comfort", params.comfort),
            asp.fact("chosen_adjective", params.adjective),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "chosen_ok")) and not bool(asp.atoms(model, "bad_choice"))


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
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
        if not asp_choice_ok(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome and validity match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} ASP scenario checks failed.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a goose, a truthful adjective, and a woven comfort item."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--adjective", choices=ADJECTIVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--goose-name")
    ap.add_argument("--helper", choices=["grandpa", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.obstacle not in PLACES[args.place].affords:
        raise StoryError(
            f"(No story: {PLACES[args.place].label} does not include {OBSTACLES[args.obstacle].label} in this world.)"
        )
    if args.obstacle and args.comfort:
        obstacle = OBSTACLES[args.obstacle]
        comfort = COMFORTS[args.comfort]
        if not comfort_works(obstacle, comfort):
            raise StoryError(explain_comfort(obstacle, comfort))
    if args.obstacle and args.adjective:
        obstacle = OBSTACLES[args.obstacle]
        adjective = ADJECTIVES[args.adjective]
        if adjective.ending != obstacle.outcome:
            raise StoryError(explain_adjective(obstacle, adjective))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.comfort is None or combo[2] == args.comfort)
        and (args.adjective is None or combo[3] == args.adjective)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, comfort, adjective = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    goose_name = args.goose_name or rng.choice(GOOSE_NAMES)
    helper = args.helper or rng.choice(["grandpa", "aunt"])
    return StoryParams(
        place=place,
        obstacle=obstacle,
        comfort=comfort,
        adjective=adjective,
        child_name=child_name,
        child_gender=child_gender,
        goose_name=goose_name,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if params.adjective not in ADJECTIVES:
        raise StoryError(f"(Unknown adjective: {params.adjective})")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    comfort = COMFORTS[params.comfort]
    adjective = ADJECTIVES[params.adjective]

    if params.obstacle not in place.affords:
        raise StoryError(f"(No story: {place.label} does not fit {obstacle.label} here.)")
    if not comfort_works(obstacle, comfort):
        raise StoryError(explain_comfort(obstacle, comfort))
    if adjective.ending != obstacle.outcome:
        raise StoryError(explain_adjective(obstacle, adjective))

    world = tell(
        place=place,
        obstacle=obstacle,
        comfort=comfort,
        adjective=adjective,
        child_name=params.child_name,
        child_gender=params.child_gender,
        goose_name=params.goose_name,
        helper_type=params.helper,
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
        print(f"{len(combos)} compatible (place, obstacle, comfort, adjective) combos:\n")
        for place, obstacle, comfort, adjective in combos:
            print(f"  {place:12} {obstacle:12} {comfort:14} {adjective}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.child_name} & {p.goose_name}: {p.obstacle} at {p.place} "
                f"with {p.comfort} -> {p.adjective}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
