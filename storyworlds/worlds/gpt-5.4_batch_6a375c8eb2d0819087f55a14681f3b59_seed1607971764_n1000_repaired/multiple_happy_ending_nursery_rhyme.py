#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py
=================================================================

A small nursery-rhyme-style story world about a child launching multiple little
boats into running water, feeling a flutter of worry when they drift toward a
drain or grate, and a calm helper choosing a gentle, sensible rescue. Every
valid story ends happily, but the ending image changes with the rescue and the
safe place the boats reach.

Run it
------
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py --place garden_rill --boat paper --rescue toy_net
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py --place bath_runlet --boat paper --rescue wooden_spoon
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/multiple_happy_ending_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "sister", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "brother", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "gran",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    scene: str
    water_name: str
    start_line: str
    hazard: str
    hazard_the: str
    current: int
    safe_spot: str
    rhyme_close: str
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
class BoatKind:
    id: str
    label: str
    phrase: str
    material: str
    delicate: int
    fold_line: str
    splash_line: str
    plural_word: str
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
class Rescue:
    id: str
    label: str
    sense: int
    power: int
    gentleness: int
    action: str
    ending_image: str
    qa_text: str
    harbor: str
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


def _r_drift(world: World) -> list[str]:
    fleet = world.entities.get("fleet")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if fleet is None or child is None or helper is None:
        return []
    if fleet.meters["adrift"] < THRESHOLD or fleet.meters["rescued"] >= THRESHOLD:
        return []
    if world.place.current <= 0:
        return []
    sig = ("drift", world.place.id, fleet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fleet.meters["near_hazard"] += 1
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    return ["__drift__"]


def _r_relief(world: World) -> list[str]:
    fleet = world.entities.get("fleet")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if fleet is None or child is None or helper is None:
        return []
    if fleet.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief", fleet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["relief"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def hazard_at_risk(place: Place, boat: BoatKind) -> bool:
    return place.current > 0 and boat.delicate >= 0


def rescue_works(rescue: Rescue, place: Place, boat: BoatKind) -> bool:
    return (
        rescue.sense >= SENSE_MIN
        and rescue.power >= place.current
        and rescue.gentleness >= boat.delicate
    )


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for boat_id, boat in BOATS.items():
            if not hazard_at_risk(place, boat):
                continue
            for rescue_id, rescue in RESCUES.items():
                if rescue_works(rescue, place, boat):
                    combos.append((place_id, boat_id, rescue_id))
    return combos


def predict_drift(world: World) -> dict:
    sim = world.copy()
    fleet = sim.get("fleet")
    fleet.meters["adrift"] += 1
    propagate(sim, narrate=False)
    return {
        "near_hazard": fleet.meters["near_hazard"] >= THRESHOLD,
        "hazard": sim.place.hazard_the,
        "current": sim.place.current,
    }


def _do_launch(world: World, narrate: bool = True) -> None:
    fleet = world.get("fleet")
    fleet.meters["adrift"] += 1
    propagate(world, narrate=narrate)


def child_count_phrase(count: int) -> str:
    mapping = {
        2: "two little boats",
        3: "three little boats",
        4: "four little boats",
    }
    return mapping.get(count, f"{count} little boats")


def introduce(world: World, child: Entity, helper: Entity, boat: BoatKind, count: int) -> None:
    world.say(
        f"Little {child.id} by {world.place.scene}, "
        f"with {helper.label_word} close and kind, "
        f"made {child_count_phrase(count)} from {boat.material} bright, "
        f"for a merry floating mind."
    )
    world.say(
        f"They were multiple little sailors all in a row. "
        f"{boat.fold_line}"
    )


def launch(world: World, child: Entity, boat: BoatKind, count: int) -> None:
    fleet = world.get("fleet")
    child.memes["joy"] += 1
    world.say(
        f"Into {world.place.water_name} went one, then two, then {count} in all. "
        f"{boat.splash_line}"
    )
    _do_launch(world, narrate=False)
    if fleet.meters["near_hazard"] >= THRESHOLD:
        world.say(
            f"But the quick little water gave a tug and a glide, "
            f"and the boats began drifting toward {world.place.hazard_the}."
        )


def warn(world: World, helper: Entity, child: Entity) -> None:
    pred = predict_drift(world)
    world.facts["predicted_hazard"] = pred["hazard"]
    world.facts["predicted_current"] = pred["current"]
    if pred["near_hazard"]:
        world.say(
            f'"Steady now," said {helper.label_word}. "See how the streamlet curls? '
            f'If we let them hurry on, they will bump at {pred["hazard"]}."'
        )
        world.say(
            f"{child.id} watched with a small round mouth. "
            f"The game was still lovely, but worry fluttered in beside the joy."
        )


def rescue(world: World, helper: Entity, rescue_cfg: Rescue) -> None:
    fleet = world.get("fleet")
    helper.memes["calm"] += 1
    fleet.meters["rescued"] += 1
    fleet.meters["near_hazard"] = 0.0
    fleet.attrs["harbor"] = rescue_cfg.harbor
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {rescue_cfg.action}, "
        f"and each little boat bobbed safe at {rescue_cfg.harbor}."
    )


def cheer(world: World, child: Entity, helper: Entity, boat: BoatKind, count: int, rescue_cfg: Rescue) -> None:
    child.memes["gratitude"] += 1
    helper.memes["love"] += 1
    harbor = world.get("fleet").attrs.get("harbor", rescue_cfg.harbor)
    world.say(
        f'{child.id} clapped {child.pronoun("possessive")} hands. '
        f'"Hooray for my {child_count_phrase(count)}!" {child.pronoun()} cried.'
    )
    world.say(
        f"Soon the {boat.plural_word} were rocking softly at {harbor}, "
        f"and {rescue_cfg.ending_image}."
    )
    world.say(world.place.rhyme_close)


def tell(
    place: Place,
    boat: BoatKind,
    rescue_cfg: Rescue,
    *,
    child_name: str = "May",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    count: int = 3,
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            label=child_name,
            traits=["little", "busy"],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={},
        )
    )
    fleet = world.add(
        Entity(
            id="fleet",
            kind="thing",
            type="boats",
            label="boats",
            phrase=boat.phrase,
            attrs={"count": count, "material": boat.material, "plural": True, "harbor": ""},
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        boat_cfg=boat,
        rescue_cfg=rescue_cfg,
        count=count,
        place=place,
        predicted_hazard="",
        predicted_current=0,
    )

    introduce(world, child, helper, boat, count)
    world.para()
    launch(world, child, boat, count)
    warn(world, helper, child)
    world.para()
    rescue(world, helper, rescue_cfg)
    cheer(world, child, helper, boat, count, rescue_cfg)

    world.facts.update(
        harbor=fleet.attrs.get("harbor", rescue_cfg.harbor),
        worried=child.memes["relief"] >= THRESHOLD,
        safe=fleet.meters["rescued"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden_rill": Place(
        id="garden_rill",
        scene="the garden rill",
        water_name="the silver rill",
        start_line="by the beans and marigolds",
        hazard="a grate by the stepping stones",
        hazard_the="the grate by the stepping stones",
        current=2,
        safe_spot="the mossy bank",
        rhyme_close="So the song ran light through the garden still, and the day stayed sweet by the little rill.",
        tags={"rill", "water"},
    ),
    "courtyard_runoff": Place(
        id="courtyard_runoff",
        scene="the courtyard after rain",
        water_name="the rain-run ribbon",
        start_line="by the red brick wall",
        hazard="a small drain in the yard",
        hazard_the="the small drain in the yard",
        current=1,
        safe_spot="the sun-warm curb",
        rhyme_close="Then puddle and pebble and brick all shone, and the boats kept dancing safe on their own.",
        tags={"puddle", "drain", "water"},
    ),
    "bath_runlet": Place(
        id="bath_runlet",
        scene="the warm bath rim",
        water_name="the bath-side runlet",
        start_line="by the soap dish",
        hazard="the plughole in the tub",
        hazard_the="the plughole in the tub",
        current=2,
        safe_spot="the dry enamel side",
        rhyme_close="And splash by splash in the candle-light, the bath-time boats came home all right.",
        tags={"bath", "plughole", "water"},
    ),
}

BOATS = {
    "paper": BoatKind(
        id="paper",
        label="paper boats",
        phrase="folded paper boats",
        material="paper",
        delicate=2,
        fold_line="Crisp little corners kissed into peaks, with white bright noses and tidy cheeks.",
        splash_line="They dipped and tipped with a whispery sway, like tiny geese in a holiday play.",
        plural_word="paper boats",
        tags={"paper_boat", "boat"},
    ),
    "leaf": BoatKind(
        id="leaf",
        label="leaf boats",
        phrase="leaf boats",
        material="broad green leaves",
        delicate=1,
        fold_line="Each leaf was curled with a stem for a mast, a trim green craft both nimble and fast.",
        splash_line="They skipped on the water with shiny green backs, twirling like dancers on watery tracks.",
        plural_word="leaf boats",
        tags={"leaf_boat", "boat"},
    ),
    "bark": BoatKind(
        id="bark",
        label="bark boats",
        phrase="little bark boats",
        material="thin bark",
        delicate=0,
        fold_line="Bark chips were smoothed with a careful thumb, stout little ships with a hummable hum.",
        splash_line="They bobbed with a plunk and a proud little knock, like toy boats knocking on toy harbor rock.",
        plural_word="bark boats",
        tags={"bark_boat", "boat"},
    ),
}

RESCUES = {
    "toy_net": Rescue(
        id="toy_net",
        label="toy net",
        sense=3,
        power=2,
        gentleness=2,
        action="reached out with a toy net, scooped under the floating noses one by one",
        ending_image="their damp edges shone like moons in a row",
        qa_text="used a toy net to scoop the boats up one by one",
        harbor="the waiting washbasin",
        tags={"net", "rescue_tool"},
    ),
    "twig_bridge": Rescue(
        id="twig_bridge",
        label="twig bridge",
        sense=2,
        power=1,
        gentleness=2,
        action="laid a twig across the tiny flow, making a bridge that turned the boats aside",
        ending_image="they nudged together like ducklings at rest",
        qa_text="laid a twig bridge to turn the boats away from danger",
        harbor="the mossy bank",
        tags={"twig_bridge", "rescue_tool"},
    ),
    "wooden_spoon": Rescue(
        id="wooden_spoon",
        label="wooden spoon",
        sense=2,
        power=2,
        gentleness=1,
        action="slid a wooden spoon under the little hulls and guided them toward the side",
        ending_image="the wooden spoon dripped while the boats sat proud and dry enough to sail again",
        qa_text="used a wooden spoon to guide the boats safely to the side",
        harbor="the dry enamel side",
        tags={"spoon", "rescue_tool"},
    ),
    "quick_hands": Rescue(
        id="quick_hands",
        label="quick hands",
        sense=1,
        power=1,
        gentleness=0,
        action="snatched at the boats with quick hands",
        ending_image="the boats came out crumpled",
        qa_text="grabbed at the boats with quick hands",
        harbor="the helper's wet palm",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["May", "Dot", "Nell", "Molly", "Poppy", "Elsie", "Rose", "Kit"]
BOY_NAMES = ["Tom", "Ned", "Will", "Bram", "Jem", "Toby", "Finn", "Milo"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
COUNTS = [2, 3, 4]


@dataclass
class StoryParams:
    place: str
    boat: str
    rescue: str
    child_name: str
    child_type: str
    helper_type: str
    count: int = 3
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


CURATED = [
    StoryParams(
        place="garden_rill",
        boat="paper",
        rescue="toy_net",
        child_name="May",
        child_type="girl",
        helper_type="grandmother",
        count=3,
    ),
    StoryParams(
        place="courtyard_runoff",
        boat="leaf",
        rescue="twig_bridge",
        child_name="Ned",
        child_type="boy",
        helper_type="father",
        count=4,
    ),
    StoryParams(
        place="bath_runlet",
        boat="bark",
        rescue="wooden_spoon",
        child_name="Dot",
        child_type="girl",
        helper_type="mother",
        count=2,
    ),
    StoryParams(
        place="garden_rill",
        boat="leaf",
        rescue="toy_net",
        child_name="Will",
        child_type="boy",
        helper_type="grandfather",
        count=4,
    ),
    StoryParams(
        place="courtyard_runoff",
        boat="paper",
        rescue="toy_net",
        child_name="Poppy",
        child_type="girl",
        helper_type="mother",
        count=3,
    ),
]

KNOWLEDGE = {
    "boat": [
        (
            "What is a little toy boat?",
            "A toy boat is a small boat made for play. It can float on water if it is light enough and shaped to hold itself up.",
        )
    ],
    "paper_boat": [
        (
            "Why can paper boats be delicate?",
            "Paper boats float nicely at first, but paper softens when it gets very wet. That is why they need a gentle rescue.",
        )
    ],
    "leaf_boat": [
        (
            "Why do leaf boats float?",
            "Leaves are light and spread out on the water. They can bob along like tiny green rafts.",
        )
    ],
    "bark_boat": [
        (
            "Why is bark good for a little boat?",
            "Thin bark is sturdier than paper and can stay afloat for longer. It still needs calm water and careful hands.",
        )
    ],
    "drain": [
        (
            "What is a drain for?",
            "A drain lets water run away. Small things can be carried toward it if the water is moving fast.",
        )
    ],
    "plughole": [
        (
            "What is a plughole?",
            "A plughole is the hole where bath water drains out. Tiny floating things can drift toward it if the water starts to run that way.",
        )
    ],
    "net": [
        (
            "What does a little net do?",
            "A net can scoop floating things out of water. It helps lift them gently instead of squashing them.",
        )
    ],
    "twig_bridge": [
        (
            "How can a twig help a tiny boat?",
            "A twig can make a little barrier or bridge in shallow water. It can turn a small boat toward a safer edge.",
        )
    ],
    "spoon": [
        (
            "How can a spoon help in water play?",
            "A spoon can slide under something floating and guide it to the side. A smooth spoon is gentler than grabbing with fingers.",
        )
    ],
    "water": [
        (
            "Why do little things drift in moving water?",
            "Moving water pushes light things along. The stronger the current is, the faster they travel.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "boat",
    "paper_boat",
    "leaf_boat",
    "bark_boat",
    "drain",
    "plughole",
    "net",
    "twig_bridge",
    "spoon",
    "water",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    boat = f["boat_cfg"]
    place = f["place"]
    rescue_cfg = f["rescue_cfg"]
    count = f["count"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "multiple" and ends happily.',
        f"Tell a gentle rhyme-like story where little {child.id} floats {count} {boat.plural_word} in {place.water_name}, and {helper.label_word} rescues them before they drift into {place.hazard_the}.",
        f"Write a playful water story with a happy ending where {rescue_cfg.label} helps save several tiny boats and the last image feels safe and singable.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    boat = f["boat_cfg"]
    rescue_cfg = f["rescue_cfg"]
    count = f["count"]
    harbor = f["harbor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about little {child.id}, {helper.label_word}, and {count} tiny {boat.plural_word}. They begin as a cheerful floating game beside {place.scene}.",
        ),
        (
            f"What did {child.id} make?",
            f"{child.id} made {child_count_phrase(count)} from {boat.material}. The story calls them multiple little sailors because there was more than one boat bobbing along together.",
        ),
        (
            "Why did the game turn a little worrying?",
            f"The water was moving toward {place.hazard_the}, so the boats began drifting the wrong way. {helper.label_word.capitalize()} noticed the current first and understood they might be lost if nobody helped.",
        ),
        (
            f"How did {helper.label_word} save the boats?",
            f"{helper.label_word.capitalize()} {rescue_cfg.qa_text}. That worked because it was strong enough for the water and gentle enough for the {boat.plural_word}.",
        ),
        (
            "How did the story end?",
            f"It ended happily, with the boats safe at {harbor}. {child.id} could clap and cheer because the game was rescued instead of spoiled.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["boat_cfg"].tags) | set(f["place"].tags) | set(f["rescue_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or k == "count"}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, boat: BoatKind, rescue_cfg: Rescue) -> str:
    if rescue_cfg.sense < SENSE_MIN:
        return (
            f"(No story: '{rescue_cfg.id}' is known to the world, but it is too clumsy for a good child-facing rescue. "
            f"Pick a gentler, more sensible tool like toy_net, twig_bridge, or wooden_spoon.)"
        )
    if rescue_cfg.power < place.current:
        return (
            f"(No story: {rescue_cfg.label} is too weak for the water at {place.scene}. "
            f"The rescue must be strong enough to turn or lift the boats in that current.)"
        )
    if rescue_cfg.gentleness < boat.delicate:
        return (
            f"(No story: {rescue_cfg.label} is too rough for {boat.plural_word}. "
            f"The rescue must be gentle enough not to crumple or crush them.)"
        )
    return "(No story: this place, boat, and rescue do not make a reasonable combination.)"


ASP_RULES = r"""
hazard(P,B) :- place(P), boat(B), current(P,C), C > 0.

sensible(R) :- rescue(R), sense(R,S), sense_min(M), S >= M.

works(P,B,R) :- place(P), boat(B), rescue(R),
                current(P,C), power(R,Po), Po >= C,
                delicate(B,D), gentleness(R,G), G >= D,
                sensible(R).

valid(P,B,R) :- hazard(P,B), works(P,B,R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("current", place_id, place.current))
    for boat_id, boat in BOATS.items():
        lines.append(asp.fact("boat", boat_id))
        lines.append(asp.fact("delicate", boat_id, boat.delicate))
    for rescue_id, rescue_cfg in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("sense", rescue_id, rescue_cfg.sense))
        lines.append(asp.fact("power", rescue_id, rescue_cfg.power))
        lines.append(asp.fact("gentleness", rescue_id, rescue_cfg.gentleness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sensible = set(asp_sensible())
    p_sensible = {r.id for r in sensible_rescues()}
    if c_sensible == p_sensible:
        print(f"OK: sensible rescues match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        resolved = resolve_params(build_parser().parse_args([]), random.Random(123))
        resolved.seed = 123
        sample2 = generate(resolved)
        if not sample2.story.strip():
            raise StoryError("resolved smoke test generated an empty story")
        print("OK: smoke generation and emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme-style story world: multiple little boats, a quick current, and a gentle happy rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--count", type=int, choices=COUNTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.boat and args.rescue:
        place = PLACES[args.place]
        boat = BOATS[args.boat]
        rescue_cfg = RESCUES[args.rescue]
        if not rescue_works(rescue_cfg, place, boat):
            raise StoryError(explain_rejection(place, boat, rescue_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.boat is None or combo[1] == args.boat)
        and (args.rescue is None or combo[2] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, boat_id, rescue_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    default_names = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(default_names)
    helper_type = args.helper_type or rng.choice(HELPERS)
    count = args.count if args.count is not None else rng.choice(COUNTS)

    return StoryParams(
        place=place_id,
        boat=boat_id,
        rescue=rescue_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        count=count,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.boat not in BOATS:
        raise StoryError(f"(Unknown boat: {params.boat})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if params.count not in COUNTS:
        raise StoryError(f"(Unsupported count: {params.count}; choose from {COUNTS}.)")

    place = PLACES[params.place]
    boat = BOATS[params.boat]
    rescue_cfg = RESCUES[params.rescue]
    if not rescue_works(rescue_cfg, place, boat):
        raise StoryError(explain_rejection(place, boat, rescue_cfg))

    world = tell(
        place=place,
        boat=boat,
        rescue_cfg=rescue_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        count=params.count,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible rescues: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, boat, rescue) combos:\n")
        for place_id, boat_id, rescue_id in combos:
            print(f"  {place_id:17} {boat_id:8} {rescue_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.count} {p.boat} boats at {p.place} with {p.rescue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
