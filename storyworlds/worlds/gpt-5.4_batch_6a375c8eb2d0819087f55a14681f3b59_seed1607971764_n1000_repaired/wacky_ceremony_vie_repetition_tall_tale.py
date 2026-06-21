#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py
=====================================================================

A standalone story world for a tall-tale-style story about a child who wants to
vie for glory in a wacky small-town ceremony. The town's giant parade kite must
be raised for the morning sky ceremony, but the wind, the ribbon tail, and the
chosen launch method have to make sense together.

This world models:
- typed entities with physical meters and emotional memes
- a reasonableness gate over what can go wrong and which fix can honestly work
- a state-driven story with premise, tension, turn, and ending image
- repetition in the rendered prose
- an inline ASP twin for parity checks

Run it
------
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py --asp
    python storyworlds/worlds/gpt-5.4/wacky_ceremony_vie_repetition_tall_tale.py --verify
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
    airborne: bool = False
    tanglable: bool = False
    steadying: bool = False
    linewise: bool = False
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
class Festival:
    id: str
    place: str
    landmark: str
    crowd: str
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
class KiteKind:
    id: str
    label: str
    phrase: str
    boast: str
    shape_line: str
    tail_name: str
    wind_need: int
    fussiness: int
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
class Wind:
    id: str
    label: str
    opening: str
    strength: int
    knots_tail: bool
    help_text: str
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
class LaunchMethod:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    style: str
    fail_text: str
    success_text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"boaster", "helper"}]

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


def _r_knot_trouble(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    tail = world.get("tail")
    if tail.meters["knotted"] < THRESHOLD:
        return out
    sig = ("knot_trouble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite.meters["lift_loss"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__knot__")
    return out


def _r_ground_drag(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    if kite.meters["grounded"] < THRESHOLD:
        return out
    sig = ("ground_drag",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite.meters["dusty"] += 1
    world.get("tail").meters["dragged"] += 1
    out.append("__drag__")
    return out


def _r_airborne_joy(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    if kite.meters["airborne"] < THRESHOLD:
        return out
    sig = ("airborne_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.get("crowd").memes["cheer"] += 1
    out.append("__lift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="knot_trouble", tag="physical", apply=_r_knot_trouble),
    Rule(name="ground_drag", tag="physical", apply=_r_ground_drag),
    Rule(name="airborne_joy", tag="social", apply=_r_airborne_joy),
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


def enough_wind(kite: KiteKind, wind: Wind) -> bool:
    return wind.strength >= kite.wind_need


def hazard_at_risk(kite: KiteKind, wind: Wind) -> bool:
    return enough_wind(kite, wind) and wind.knots_tail and kite.fussiness >= 1


def sensible_methods() -> list[LaunchMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def launch_difficulty(kite: KiteKind, wind: Wind) -> int:
    return kite.fussiness + max(0, wind.strength - kite.wind_need)


def method_contains(method: LaunchMethod, kite: KiteKind, wind: Wind) -> bool:
    return method.power >= launch_difficulty(kite, wind)


def predict_kite(world: World, method_id: str) -> dict:
    sim = world.copy()
    method = METHODS[method_id]
    _attempt_launch(sim, method, narrate=False)
    return {
        "airborne": sim.get("kite").meters["airborne"] >= THRESHOLD,
        "tail_knotted": sim.get("tail").meters["knotted"] >= THRESHOLD,
        "grounded": sim.get("kite").meters["grounded"] >= THRESHOLD,
    }


def introduce(world: World, festival: Festival, boaster: Entity, helper: Entity,
              parent: Entity, kite_cfg: KiteKind, wind: Wind) -> None:
    boaster.memes["pride"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In {festival.place}, folks held the Sunrise String Ceremony every year, "
        f"and it was the wackiest ceremony for fifty fences in every direction."
    )
    world.say(
        f"At dawn, the townspeople gathered by {festival.landmark}. {wind.opening} "
        f"{festival.crowd}"
    )
    world.say(
        f"Right in the middle waited {kite_cfg.phrase}, {kite_cfg.shape_line} "
        f"{kite_cfg.boast}"
    )
    world.say(
        f"{boaster.id} and {helper.id} had come to vie for the honor of helping lift it, "
        f"while {boaster.id}'s {parent.label_word} held the spool and watched."
    )


def boast(world: World, boaster: Entity, helper: Entity, kite_cfg: KiteKind) -> None:
    boaster.memes["bravado"] += 1
    world.say(
        f'"I can send that {kite_cfg.label} up all by myself," {boaster.id} said. '
        f'"Up, up, up it will go!"'
    )
    world.say(
        f'{helper.id} squinted at the tail and said, "Maybe. But that long '
        f'{kite_cfg.tail_name} looks like it wants to twist and twist and twist."'
    )


def ceremony_need(world: World, festival: Festival, parent: Entity) -> None:
    world.say(
        f'Without the kite in the sky, the ceremony could not begin, because the town band '
        f'never played a note until a bright ribbon shape floated over {festival.landmark}.'
    )
    world.say(
        f'"Easy and steady," said {parent.label_word}. "The sky likes patience better than bragging."'
    )


def tangle(world: World, wind: Wind, kite_cfg: KiteKind) -> None:
    tail = world.get("tail")
    tail.meters["knotted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the moment the wind gave a sideways yank, the {kite_cfg.tail_name} whipped "
        f"around itself. It twisted and twisted and twisted until it looked like a rainbow pretzel."
    )
    world.say(
        f"The big {kite_cfg.label} heaved once, then sagged back down. Even a kite that size "
        f"could not climb with a snarled tail."
    )


def warn(world: World, helper: Entity, boaster: Entity, parent: Entity,
         method_id: str, kite_cfg: KiteKind, wind: Wind) -> None:
    pred = predict_kite(world, method_id)
    helper.memes["care"] += 1
    world.facts["predicted_airborne"] = pred["airborne"]
    if not pred["airborne"]:
        world.say(
            f'{helper.id} tugged {boaster.id}\'s sleeve. "{boaster.id}, if you just {METHODS[method_id].label}, '
            f'the knots will keep that {kite_cfg.label} on the ground."'
        )
        world.say(
            f'{parent.label_word.capitalize()} nodded. "This wind is strong enough to help, '
            f'but only if we make the tail behave first."'
        )


def choose_wrong(world: World, boaster: Entity, method: LaunchMethod) -> None:
    boaster.memes["defiance"] += 1
    world.say(
        f'"I do not need any fussing," {boaster.id} said. "I will {method.label}, '
        f'and the sky will do the rest."'
    )


def _attempt_launch(world: World, method: LaunchMethod, narrate: bool = True) -> None:
    kite = world.get("kite")
    if world.get("tail").meters["knotted"] >= THRESHOLD and method.id != "comb_and_run":
        kite.meters["grounded"] += 1
        propagate(world, narrate=narrate)
        return
    if method.id == "comb_and_run":
        world.get("tail").meters["knotted"] = 0.0
        world.get("tail").meters["straightened"] += 1
        kite.meters["ready"] += 1
    if world.facts["wind"].strength < world.facts["kite_cfg"].wind_need:
        kite.meters["grounded"] += 1
        propagate(world, narrate=narrate)
        return
    if method_contains(method, world.facts["kite_cfg"], world.facts["wind"]):
        kite.meters["airborne"] += 1
    else:
        kite.meters["grounded"] += 1
    propagate(world, narrate=narrate)


def fail_launch(world: World, boaster: Entity, method: LaunchMethod, kite_cfg: KiteKind) -> None:
    _attempt_launch(world, method, narrate=False)
    world.say(
        method.fail_text.replace("{name}", boaster.id).replace("{kite}", kite_cfg.label)
    )
    world.say(
        f"The {kite_cfg.label} skidded over the grass and puffed up a dust cloud broad enough "
        f"to make three chickens sneeze."
    )


def rethink(world: World, boaster: Entity, helper: Entity) -> None:
    boaster.memes["humility"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{boaster.id} stared at the knotted tail, then at the waiting crowd. "
        f"For the first time that morning, {boaster.pronoun()} stopped boasting."
    )
    world.say(
        f'"All right," {boaster.pronoun()} said. "Show me the careful way."'
    )


def fix_and_launch(world: World, boaster: Entity, helper: Entity, parent: Entity,
                   method: LaunchMethod, festival: Festival, kite_cfg: KiteKind) -> None:
    _attempt_launch(world, method, narrate=False)
    boaster.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} ran fingers through the tail, ribbon by ribbon, while {parent.label_word} "
        f"kept the spool steady and {boaster.id} backed away with the line."
    )
    world.say(
        f"Then they all did it together: they pulled and pulled and pulled, "
        f"and {method.success_text.replace('{kite}', kite_cfg.label)}."
    )
    world.say(
        f"Up rose the {kite_cfg.label}, over the fence and the feed shed and the tallest weather vane, "
        f"until its tail wrote bright loops across the morning."
    )
    world.say(
        f'The band struck up at once, and the whole crowd shouted, "{festival.sendoff}!"'
    )


def ending(world: World, boaster: Entity, helper: Entity, festival: Festival,
           kite_cfg: KiteKind) -> None:
    boaster.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"After that, whenever children in {festival.place} came to vie for a turn in the sky, "
        f"they remembered that even a wacky ceremony works best with more than one pair of hands."
    )
    world.say(
        f"And every year the townspeople pointed upward and said the same thing: "
        f'"There goes the {kite_cfg.label}, high and higher and highest of all."'
    )


def tell(festival: Festival, kite_cfg: KiteKind, wind: Wind, wrong_method: LaunchMethod,
         fix_method: LaunchMethod, boaster_name: str = "Mae", boaster_gender: str = "girl",
         helper_name: str = "Jeb", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    boaster = world.add(Entity(
        id=boaster_name,
        kind="character",
        type=boaster_gender,
        role="boaster",
        attrs={"eager": True},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        attrs={"careful": True},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="adult",
        label="the parent",
    ))
    kite = world.add(Entity(
        id="kite",
        type="kite",
        label=kite_cfg.label,
        airborne=True,
        attrs={"tail_name": kite_cfg.tail_name},
    ))
    tail = world.add(Entity(
        id="tail",
        type="tail",
        label=kite_cfg.tail_name,
        tanglable=True,
        linewise=True,
    ))
    crowd = world.add(Entity(
        id="crowd",
        type="crowd",
        label="the crowd",
        role="crowd",
    ))

    world.facts.update(
        festival=festival,
        kite_cfg=kite_cfg,
        wind=wind,
        wrong_method=wrong_method,
        fix_method=fix_method,
        boaster=boaster,
        helper=helper,
        parent=parent,
        outcome="",
        problem="",
    )

    introduce(world, festival, boaster, helper, parent, kite_cfg, wind)
    world.para()
    boast(world, boaster, helper, kite_cfg)
    ceremony_need(world, festival, parent)

    if wind.knots_tail:
        world.para()
        tangle(world, wind, kite_cfg)
        warn(world, helper, boaster, parent, wrong_method.id, kite_cfg, wind)

    world.para()
    choose_wrong(world, boaster, wrong_method)
    fail_launch(world, boaster, wrong_method, kite_cfg)
    world.facts["problem"] = "tail_knotted"

    world.para()
    rethink(world, boaster, helper)
    fix_and_launch(world, boaster, helper, parent, fix_method, festival, kite_cfg)

    world.para()
    ending(world, boaster, helper, festival, kite_cfg)
    world.facts["outcome"] = "launched"
    world.facts["airborne"] = world.get("kite").meters["airborne"] >= THRESHOLD
    world.facts["tail_straight"] = world.get("tail").meters["straightened"] >= THRESHOLD
    return world


FESTIVALS = {
    "prairie": Festival(
        id="prairie",
        place="Prairie Junction",
        landmark="the water tower",
        crowd="Cows leaned over fences, and even the fence posts looked ready to clap.",
        sendoff="Let the morning fly",
        tags={"ceremony", "town"},
    ),
    "mesa": Festival(
        id="mesa",
        place="Red Mesa Crossing",
        landmark="the old stone well",
        crowd="Mules blinked from the shade, and hats bobbed like a field of mushrooms.",
        sendoff="Let the morning fly",
        tags={"ceremony", "town"},
    ),
    "river": Festival(
        id="river",
        place="Big River Bend",
        landmark="the creaky grain elevator",
        crowd="Dogs barked, ducks quacked, and every porch seemed to lean closer.",
        sendoff="Let the morning fly",
        tags={"ceremony", "town"},
    ),
}

KITES = {
    "rooster": KiteKind(
        id="rooster",
        label="rooster kite",
        phrase="a rooster kite as wide as a wagon shed",
        boast="Its painted beak looked bold enough to peck the sun awake.",
        shape_line="Its red comb flapped like a flag,",
        tail_name="ribbon tail",
        wind_need=2,
        fussiness=1,
        tags={"kite", "bird"},
    ),
    "catfish": KiteKind(
        id="catfish",
        label="catfish kite",
        phrase="a catfish kite longer than a fishing boat",
        boast="Its whiskers were so long they tickled the drummer from ten steps off.",
        shape_line="Its silver belly gleamed like a creek at noon,",
        tail_name="streamer whiskers",
        wind_need=2,
        fussiness=2,
        tags={"kite", "fish"},
    ),
    "mooncow": KiteKind(
        id="mooncow",
        label="moon-cow kite",
        phrase="a moon-cow kite spotted like the night sky",
        boast="Folks said it could graze on clouds if you let the line out too far.",
        shape_line="Its horns curled like crescent moons,",
        tail_name="starry tail",
        wind_need=3,
        fussiness=2,
        tags={"kite", "sky"},
    ),
}

WINDS = {
    "brisk": Wind(
        id="brisk",
        label="brisk wind",
        opening="A brisk wind skipped over the grass and rattled every tin bucket in town.",
        strength=2,
        knots_tail=True,
        help_text="The wind can lift a big kite, but it can also twist a long tail.",
        tags={"wind"},
    ),
    "gusty": Wind(
        id="gusty",
        label="gusty wind",
        opening="A gusty wind came bouncing through town, strong enough to wobble the church bell rope.",
        strength=3,
        knots_tail=True,
        help_text="Strong gusts help with lift but punish sloppy tails.",
        tags={"wind"},
    ),
    "howling": Wind(
        id="howling",
        label="howling wind",
        opening="A howling wind rolled across the ground so loudly that hats had to hang on with both hands.",
        strength=4,
        knots_tail=True,
        help_text="A howling wind can launch anything that is straight and ready.",
        tags={"wind"},
    ),
    "lazy": Wind(
        id="lazy",
        label="lazy wind",
        opening="A lazy wind drifted along as if it had all summer to get anywhere at all.",
        strength=1,
        knots_tail=False,
        help_text="A lazy wind will not lift the big ceremonial kites.",
        tags={"wind"},
    ),
}

METHODS = {
    "yank": LaunchMethod(
        id="yank",
        label="give the line one mighty yank",
        phrase="one mighty yank",
        power=1,
        sense=1,
        style="rash",
        fail_text="{name} planted both heels, gave the line one mighty yank, and the {kite} only bumped the ground harder.",
        success_text="the wind caught it after the yank",
        qa_text="tried to launch it with one mighty yank",
        tags={"kite", "wind"},
    ),
    "run": LaunchMethod(
        id="run",
        label="run at the field and heave",
        phrase="a running heave",
        power=2,
        sense=2,
        style="bold",
        fail_text="{name} ran hard enough to kick up grass clods, heaved on the line, and the {kite} only lurched sideways.",
        success_text="the wind finally took hold of the {kite}",
        qa_text="ran with the line and heaved the kite up",
        tags={"kite", "wind"},
    ),
    "comb_and_run": LaunchMethod(
        id="comb_and_run",
        label="comb the tail straight and run together",
        phrase="a careful comb-and-run launch",
        power=4,
        sense=3,
        style="careful",
        fail_text="{name} tried the careful launch, but the sky still would not take the {kite}",
        success_text="the wind slid through the tail and lifted the {kite}",
        qa_text="straightened the tail and launched it together",
        tags={"kite", "teamwork"},
    ),
}

GIRL_NAMES = ["Mae", "Tilly", "June", "Ada", "Lula", "Pearl", "Nell", "Dora"]
BOY_NAMES = ["Jeb", "Cal", "Eli", "Hank", "Otis", "Beau", "Wade", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_methods():
        return combos
    for festival_id in FESTIVALS:
        for kite_id, kite in KITES.items():
            for wind_id, wind in WINDS.items():
                if hazard_at_risk(kite, wind):
                    combos.append((festival_id, kite_id, wind_id))
    return combos


@dataclass
class StoryParams:
    festival: str = "prairie"
    kite: str = "rooster"
    wind: str = "brisk"
    wrong_method: str = "run"
    fix_method: str = "comb_and_run"
    boaster: str = "Mae"
    boaster_gender: str = "girl"
    helper: str = "Jeb"
    helper_gender: str = "boy"
    parent: str = "mother"
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
    "ceremony": [
        (
            "What is a ceremony?",
            "A ceremony is a special event people do in a certain way to mark an important moment. It often has music, watching, and a part everyone waits for."
        )
    ],
    "vie": [
        (
            "What does vie mean?",
            "Vie means to try hard against someone else for the same honor or prize. People who vie both want the turn very much."
        )
    ],
    "kite": [
        (
            "How does a kite fly?",
            "A kite flies when moving air pushes against it while someone holds the line. The shape catches the wind and lifts it up into the sky."
        )
    ],
    "wind": [
        (
            "Why can wind make a kite hard to launch?",
            "Wind can help a kite rise, but it can also twist ribbons and tails if they are loose. A strong gust helps best when the kite is straight and ready."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful for a big job?",
            "Teamwork helps because one person can steady, another can fix, and another can pull at the right time. Big jobs often go better when people share the work."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    boaster = f["boaster"]
    helper = f["helper"]
    festival = f["festival"]
    kite_cfg = f["kite_cfg"]
    return [
        (
            f'Write a tall-tale story for a 3-to-5-year-old that uses the words '
            f'"wacky," "ceremony," and "vie," and includes repetition.'
        ),
        (
            f"Tell a playful frontier-style story where {boaster.id} and {helper.id} vie "
            f"to help at a town ceremony, but a giant {kite_cfg.label} will not rise until "
            f"someone stops boasting and starts working together."
        ),
        (
            f"Write a tall tale set in {festival.place} where a wacky sunrise ceremony depends "
            f"on a huge kite, and the ending shows the whole town seeing what changed."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    boaster = f["boaster"]
    helper = f["helper"]
    parent = f["parent"]
    festival = f["festival"]
    kite_cfg = f["kite_cfg"]
    wrong_method = f["wrong_method"]
    fix_method = f["fix_method"]
    wind = f["wind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {boaster.id} and {helper.id}, two children in {festival.place} who wanted to vie for a special turn at the sunrise ceremony. {boaster.id}'s {parent.label_word} was there too, helping hold the line steady."
        ),
        (
            "What made the ceremony wacky?",
            f"The town used an enormous {kite_cfg.label} instead of something small and ordinary. In this tall tale, the kite was so huge it sounded bigger than barns and wagon sheds."
        ),
        (
            f"Why was the giant {kite_cfg.label} important?",
            f"The band would not begin the ceremony until the kite floated over {festival.landmark}. Getting it into the sky was the signal that the celebration could start."
        ),
        (
            f"What problem stopped the kite from rising at first?",
            f"The {kite_cfg.tail_name} twisted into knots when the {wind.label} yanked it sideways. A knotted tail made the kite lose lift, so it sagged back to the ground instead of climbing."
        ),
        (
            f"Why did {boaster.id}'s first plan fail?",
            f"{boaster.id} tried to {wrong_method.label}, but that did not fix the tangled tail. The wind was strong enough to help, yet the knots kept the kite grounded."
        ),
        (
            "How did they solve the problem?",
            f"They stopped rushing, straightened the tail ribbon by ribbon, and then used a careful launch together. That worked because the tail was no longer tangled, so the wind could lift the kite instead of fighting it."
        ),
        (
            f"How did {boaster.id} change by the end?",
            f"{boaster.id} began the morning bragging and trying to do everything alone. By the end, {boaster.pronoun()} trusted {helper.id} and learned that even a wacky ceremony works better with teamwork."
        ),
    ]
    if world.facts.get("airborne"):
        qa.append(
            (
                "How did the story end?",
                f"The kite finally rose high over the town, and the band started playing at once. The ending image shows everyone looking up together and seeing the ceremony succeed."
            )
        )
    if fix_method.id == "comb_and_run":
        qa.append(
            (
                f"Who helped most when the turn came?",
                f"{helper.id} carefully straightened the tail while {parent.label_word} steadied the spool and {boaster.id} held the line. The launch worked because each person handled part of the job."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ceremony", "vie", "kite", "wind", "teamwork"}
    out: list[tuple[str, str]] = []
    for key in ["ceremony", "vie", "kite", "wind", "teamwork"]:
        if key in tags:
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="prairie",
        kite="rooster",
        wind="brisk",
        wrong_method="run",
        fix_method="comb_and_run",
        boaster="Mae",
        boaster_gender="girl",
        helper="Jeb",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        festival="mesa",
        kite="catfish",
        wind="gusty",
        wrong_method="run",
        fix_method="comb_and_run",
        boaster="Cal",
        boaster_gender="boy",
        helper="June",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        festival="river",
        kite="mooncow",
        wind="howling",
        wrong_method="run",
        fix_method="comb_and_run",
        boaster="Pearl",
        boaster_gender="girl",
        helper="Finn",
        helper_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(kite: KiteKind, wind: Wind) -> str:
    if not enough_wind(kite, wind):
        return (
            f"(No story: {wind.label} is too weak to lift the {kite.label}. "
            f"A ceremony story here needs a real chance for the kite to rise after the fix.)"
        )
    if not wind.knots_tail:
        return (
            f"(No story: {wind.label} does not tangle the {kite.tail_name}, so there is no honest problem for the careful fix to solve.)"
        )
    return "(No story: this combination does not form the needed launch problem.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
enough_wind(K, W) :- kite(K), wind(W), wind_need(K, N), strength(W, S), S >= N.
hazard(K, W) :- enough_wind(K, W), knots_tail(W), fussiness(K, F), F >= 1.
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(F, K, W) :- festival(F), kite(K), wind(W), hazard(K, W).

difficulty(K, W, D) :- fussiness(K, F), strength(W, S), wind_need(K, N), D = F + (S - N), S >= N.
contains(M, K, W) :- method(M), power(M, P), difficulty(K, W, D), P >= D.

launches(K, W, M) :- chosen_kite(K), chosen_wind(W), chosen_fix(M), M = comb_and_run, contains(M, K, W).
outcome(launched) :- launches(K, W, M), chosen_kite(K), chosen_wind(W), chosen_fix(M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for kite_id, kite in KITES.items():
        lines.append(asp.fact("kite", kite_id))
        lines.append(asp.fact("wind_need", kite_id, kite.wind_need))
        lines.append(asp.fact("fussiness", kite_id, kite.fussiness))
    for wind_id, wind in WINDS.items():
        lines.append(asp.fact("wind", wind_id))
        lines.append(asp.fact("strength", wind_id, wind.strength))
        if wind.knots_tail:
            lines.append(asp.fact("knots_tail", wind_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        lines.append(asp.fact("sense", method_id, method.sense))
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
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_kite", params.kite),
            asp.fact("chosen_wind", params.wind),
            asp.fact("chosen_fix", params.fix_method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    kite = KITES[params.kite]
    wind = WINDS[params.wind]
    method = METHODS[params.fix_method]
    if method.id != "comb_and_run":
        return "?"
    return "launched" if method_contains(method, kite, wind) and hazard_at_risk(kite, wind) else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_methods = set(asp_sensible())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(clingo_methods))
        print("  python:", sorted(python_methods))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: children vie in a wacky ceremony to launch a giant kite."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--kite", choices=KITES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--wrong-method", choices=METHODS)
    ap.add_argument("--fix-method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.kite and args.wind:
        kite = KITES[args.kite]
        wind = WINDS[args.wind]
        if not hazard_at_risk(kite, wind):
            raise StoryError(explain_rejection(kite, wind))
    if args.fix_method and METHODS[args.fix_method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.fix_method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.kite is None or combo[1] == args.kite)
        and (args.wind is None or combo[2] == args.wind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, kite_id, wind_id = rng.choice(sorted(combos))
    wrong_choices = [mid for mid, method in METHODS.items() if method.id != "comb_and_run" and method.sense >= SENSE_MIN]
    wrong_method = args.wrong_method or rng.choice(sorted(wrong_choices))
    fix_method = args.fix_method or "comb_and_run"
    boaster_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if boaster_gender == "girl" else "girl"
    boaster = _pick_name(rng, boaster_gender)
    helper = _pick_name(rng, helper_gender, avoid=boaster)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        festival=festival_id,
        kite=kite_id,
        wind=wind_id,
        wrong_method=wrong_method,
        fix_method=fix_method,
        boaster=boaster,
        boaster_gender=boaster_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival: {params.festival})")
    if params.kite not in KITES:
        raise StoryError(f"(Unknown kite: {params.kite})")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind: {params.wind})")
    if params.wrong_method not in METHODS:
        raise StoryError(f"(Unknown wrong method: {params.wrong_method})")
    if params.fix_method not in METHODS:
        raise StoryError(f"(Unknown fix method: {params.fix_method})")

    kite_cfg = KITES[params.kite]
    wind = WINDS[params.wind]
    if not hazard_at_risk(kite_cfg, wind):
        raise StoryError(explain_rejection(kite_cfg, wind))
    if METHODS[params.fix_method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.fix_method))
    if METHODS[params.fix_method].id != "comb_and_run":
        raise StoryError("(The careful fix in this world must be 'comb_and_run'.)")
    if METHODS[params.wrong_method].id == "comb_and_run":
        raise StoryError("(The first choice must be a proud but imperfect method, not the careful fix.)")

    world = tell(
        festival=FESTIVALS[params.festival],
        kite_cfg=kite_cfg,
        wind=wind,
        wrong_method=METHODS[params.wrong_method],
        fix_method=METHODS[params.fix_method],
        boaster_name=params.boaster,
        boaster_gender=params.boaster_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, kite, wind) combos:\n")
        for festival_id, kite_id, wind_id in combos:
            print(f"  {festival_id:8} {kite_id:8} {wind_id}")
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
            header = f"### {p.boaster} & {p.helper}: {p.kite} at {p.festival} ({p.wind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
