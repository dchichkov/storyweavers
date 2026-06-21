#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py
===========================================================================

A standalone storyworld for a tall-tale safety story about a child who keeps
raising a sky-listening contraption "higher and higher" until a storm turns it
staticky. The world models bragging, warning, static buildup, a grounded rescue,
and a lesson learned, with an ASP twin for the reasonableness gate and outcome
parity.

Run it
------
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --place mesa --contraption kite
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --response hat_swatter
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/staticky_lesson_learned_repetition_tall_tale.py --verify
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
BOLDNESS_INIT = 6.0
HUMBLE_TRAITS = {"careful", "thoughtful", "steady"}


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
    metal: bool = False
    sky_tall: bool = False
    grounded: bool = False
    safe_sound: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandma": "grandma",
            "grandpa": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
    boast_image: str
    storm_image: str
    echo: str
    surge: int
    windy: bool = True
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
class Contraption:
    id: str
    label: str
    phrase: str
    raise_line: str
    purpose: str
    top: str
    material: str
    metal: bool
    sky_tall: bool
    spread: int
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
class SafeTool:
    id: str
    label: str
    phrase: str
    action: str
    glow: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


@dataclass
class StoryParams:
    place: str
    contraption: str
    safe_tool: str
    response: str
    name: str
    gender: str
    helper: str
    trait: str
    delay: int = 0
    pet: str = ""
    boast: str = "higher and higher"
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


def _r_static(world: World) -> list[str]:
    out: list[str] = []
    rig = world.get("rig")
    sky = world.get("sky")
    child = world.get("child")
    if rig.meters["charged"] < THRESHOLD:
        return out
    sig = ("static", rig.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sky.meters["buzz"] += 1
    child.memes["fear"] += 1
    child.meters["hair_up"] += 1
    out.append("__static__")
    return out


def _r_scorch(world: World) -> list[str]:
    out: list[str] = []
    rig = world.get("rig")
    marker = world.get("marker")
    if rig.meters["sparking"] < THRESHOLD or world.facts.get("delay", 0) < 2:
        return out
    sig = ("scorch", marker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    marker.meters["scorched"] += 1
    out.append("__scorch__")
    return out


CAUSAL_RULES = [
    Rule(name="static", tag="physical", apply=_r_static),
    Rule(name="scorch", tag="physical", apply=_r_scorch),
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


def hazard_at_risk(place: Place, contraption: Contraption) -> bool:
    return place.windy and place.surge >= 1 and contraption.metal and contraption.sky_tall


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def surge_severity(place: Place, contraption: Contraption, delay: int) -> int:
    return place.surge + contraption.spread + delay


def is_drained(response: Response, place: Place, contraption: Contraption, delay: int) -> bool:
    return response.power >= surge_severity(place, contraption, delay)


def would_averter(trait: str) -> bool:
    return trait in HUMBLE_TRAITS


def predict_static(world: World) -> dict:
    sim = world.copy()
    _do_raise(sim, narrate=False)
    rig = sim.get("rig")
    return {
        "charged": rig.meters["charged"] >= THRESHOLD,
        "hair_up": sim.get("child").meters["hair_up"] >= THRESHOLD,
        "buzz": sim.get("sky").meters["buzz"],
    }


def _do_raise(world: World, narrate: bool = True) -> None:
    rig = world.get("rig")
    rig.meters["height"] += 1
    if rig.metal and rig.sky_tall:
        rig.meters["charged"] += 1
        rig.meters["sparking"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, place: Place, contraption: Contraption) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On {place.label}, where {place.opening}, {child.id} carried {contraption.phrase} as if it were the finest listening machine west of the moon."
    )
    world.say(
        f"{helper.label_word.capitalize()} said the wind already had plenty to say, but {child.id} was sure {contraption.label} could {contraption.purpose}."
    )
    if world.facts.get("pet"):
        world.say(f"Even {world.facts['pet']} trotted along as if a whole parade were about to begin.")


def boast(world: World, child: Entity, contraption: Contraption, place: Place, boast_line: str) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"{boast_line.capitalize()}!" {child.id} cried. "{contraption.raise_line}!"'
    )
    world.say(
        f"Up went the {contraption.label}, and {place.boast_image}."
    )


def warn(world: World, child: Entity, helper: Entity, place: Place, contraption: Contraption) -> None:
    pred = predict_static(world)
    child.memes["warning_heard"] += 1
    world.facts["predicted_buzz"] = pred["buzz"]
    world.facts["predicted_hair_up"] = pred["hair_up"]
    extra = " Your hair will stand up like grass in a hard wind." if pred["hair_up"] else ""
    world.say(
        f'{helper.label_word.capitalize()} shaded {helper.pronoun("possessive")} eyes. "That sky is turning staticky," {helper.pronoun()} said. "Metal held that high can wake a blue snap from the clouds.{extra}"'
    )


def back_down(world: World, child: Entity, helper: Entity, safe_tool: SafeTool, boast_line: str) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["pride"] = 0.0
    world.say(
        f'"{boast_line.capitalize()}," {child.id} started to say again, but the words came out smaller this time.'
    )
    world.say(
        f"{child.id} looked at the darkening clouds, lowered the contraption, and nodded. Listening to {helper.label_word} felt wiser than arguing with the sky."
    )
    world.say(
        f'Together they carried it down and chose {safe_tool.phrase} instead, a thing that could {safe_tool.action} without poking at thunder.'
    )


def defy(world: World, child: Entity, helper: Entity, boast_line: str) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"{boast_line.capitalize()}!" {child.id} said again, louder than before, and gave the contraption one more proud lift.'
    )
    world.say(
        f"{helper.label_word.capitalize()} took one fast step forward, but the sky moved faster."
    )


def static_snap(world: World, child: Entity, place: Place, contraption: Contraption) -> None:
    _do_raise(world, narrate=False)
    world.say(
        f"At once the air turned woolly and staticky. {place.storm_image}, the top of the {contraption.label} crackled, and {child.id}'s hair stood up as if every strand were trying to point north."
    )
    world.say(
        f"A blue nib of spark skipped along the {contraption.material} and made {child.id} hop backward."
    )


def rescue(world: World, helper: Entity, response: Response, safe_tool: SafeTool) -> None:
    rig = world.get("rig")
    rig.meters["charged"] = 0.0
    rig.meters["sparking"] = 0.0
    rig.grounded = True
    body = response.text.replace("{rig}", rig.label)
    world.say(
        f"{helper.label_word.capitalize()} did not waste even half a heartbeat. {helper.pronoun().capitalize()} {body}."
    )
    world.say(
        f'Soon the crackle ran out of grumbles, and the whole hill went quiet except for the wind and one brave little swallow. Later, {helper.label_word} brought out {safe_tool.phrase}, which {safe_tool.glow}.'
    )


def lesson(world: World, child: Entity, helper: Entity, contraption: Contraption, boast_line: str) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} rested a hand on {child.id}\'s shoulder. "The sky can sing all by itself," {helper.pronoun()} said. "You never have to tug a metal thing up into a storm just because you want a bigger sound."'
    )
    world.say(
        f'{child.id} looked at {contraption.label} and swallowed. "I kept saying \'{boast_line},\'" {child.pronoun()} admitted. "Next time I will stop the first time the sky says no."'
    )


def rescue_fail(world: World, helper: Entity, response: Response) -> None:
    body = response.fail.replace("{rig}", world.get("rig").label)
    world.say(
        f"{helper.label_word.capitalize()} rushed in and {body}."
    )
    world.say(
        "The spark did not bite anybody, but it zipped away with a mean little hiss."
    )


def scorch_result(world: World, marker: Entity, place: Place) -> None:
    world.say(
        f"It wrote one curly black stripe across {marker.label}, a mark so crooked it looked like lightning had practiced its name there."
    )
    world.say(
        f"For the rest of the afternoon, folks on {place.label} pointed at it and said the sky had signed the day in soot."
    )


def safer_ending(world: World, child: Entity, helper: Entity, safe_tool: SafeTool, place: Place) -> None:
    child.memes["joy"] += 1
    child.memes["humble"] += 1
    world.say(
        f"The next day, under a clean sky, {child.id} and {helper.label_word} tried {safe_tool.phrase}. It could {safe_tool.action}, and {safe_tool.glow}."
    )
    world.say(
        f'This time {child.id} laughed and said, "Steady and steady," not "higher and higher," and {place.echo}.'
    )


def tell(
    place: Place,
    contraption: Contraption,
    safe_tool: SafeTool,
    response: Response,
    name: str = "June",
    gender: str = "girl",
    helper_type: str = "grandpa",
    trait: str = "careful",
    delay: int = 0,
    pet: str = "",
    boast_line: str = "higher and higher",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="child",
            traits=[trait],
            attrs={"pet": pet},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    rig = world.add(
        Entity(
            id="rig",
            type="contraption",
            label=contraption.label,
            phrase=contraption.phrase,
            metal=contraption.metal,
            sky_tall=contraption.sky_tall,
        )
    )
    sky = world.add(Entity(id="sky", type="sky", label="the sky"))
    marker = world.add(Entity(id="marker", type="marker", label="the old weather sign"))
    safe = world.add(
        Entity(
            id="safe",
            type="tool",
            label=safe_tool.label,
            phrase=safe_tool.phrase,
            safe_sound=True,
        )
    )

    world.facts["pet"] = pet
    world.facts["delay"] = delay
    world.facts["place"] = place
    world.facts["contraption_cfg"] = contraption
    world.facts["safe_tool_cfg"] = safe_tool
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["marker"] = marker
    world.facts["boast"] = boast_line

    child.memes["boldness"] = BOLDNESS_INIT
    child.memes["care"] = 5.0 if trait in HUMBLE_TRAITS else 3.0

    opening(world, child, helper, place, contraption)

    world.para()
    boast(world, child, contraption, place, boast_line)
    warn(world, child, helper, place, contraption)

    averted = would_averter(trait)
    if averted:
        back_down(world, child, helper, safe_tool, boast_line)
        world.para()
        safer_ending(world, child, helper, safe_tool, place)
        outcome = "averted"
    else:
        defy(world, child, helper, boast_line)

        world.para()
        static_snap(world, child, place, contraption)

        contained = is_drained(response, place, contraption, delay)

        world.para()
        if contained:
            rescue(world, helper, response, safe_tool)
            lesson(world, child, helper, contraption, boast_line)
            world.para()
            safer_ending(world, child, helper, safe_tool, place)
            outcome = "drained"
        else:
            rescue_fail(world, helper, response)
            propagate(world, narrate=False)
            scorch_result(world, marker, place)
            lesson(world, child, helper, contraption, boast_line)
            world.para()
            safer_ending(world, child, helper, safe_tool, place)
            outcome = "scorched"

    world.facts.update(
        place=place,
        contraption=rig,
        safe=safe,
        helper=helper,
        child=child,
        outcome=outcome,
        charged=rig.grounded or rig.meters["charged"] >= THRESHOLD or rig.meters["sparking"] >= THRESHOLD,
        scorched=marker.meters["scorched"] >= THRESHOLD,
        lessoned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "mesa": Place(
        id="mesa",
        label="the red mesa",
        opening="the grass bent low enough to whisper to rabbits",
        boast_image="it climbed so high even the crows looked up from their own business",
        storm_image="Clouds rubbed their elbows together over the mesa top",
        echo="the mesa answered with a friendly thump and not a single spark",
        surge=2,
        windy=True,
        tags={"storm", "wind", "hill"},
    ),
    "prairie": Place(
        id="prairie",
        label="the long prairie",
        opening="the fence posts leaned like old uncles listening for gossip",
        boast_image="it rose till the scarecrow looked like a button on the field",
        storm_image="The clouds bunched together like sheep with burrs in their wool",
        echo="the prairie rolled the sound away in soft, safe waves",
        surge=1,
        windy=True,
        tags={"storm", "wind", "field"},
    ),
    "ridge": Place(
        id="ridge",
        label="the high ridge",
        opening="the pines pointed upward as if they had all agreed on one grand idea",
        boast_image="it stretched so far up the hawks seemed to borrow room from it",
        storm_image="A gray belly of weather sagged over the ridge and muttered",
        echo="the ridge tossed the rhythm back as neat as a bounced ball",
        surge=3,
        windy=True,
        tags={"storm", "wind", "hill"},
    ),
    "valley": Place(
        id="valley",
        label="the sleepy valley",
        opening="the air lay still as folded blankets on a line",
        boast_image="it rose, but only enough to impress the ants",
        storm_image="Not even the clouds cared to wake up there",
        echo="the valley only yawned",
        surge=0,
        windy=False,
        tags={"calm"},
    ),
}

CONTRAPTIONS = {
    "kite": Contraption(
        id="kite",
        label="wire kite",
        phrase="a wire kite with a tail as long as a laundry day",
        raise_line="This kite will scratch a song straight out of the clouds",
        purpose="coax the wind into a tune",
        top="the kite top",
        material="wire frame",
        metal=True,
        sky_tall=True,
        spread=1,
        tags={"kite", "metal", "storm"},
    ),
    "horn": Contraption(
        id="horn",
        label="tin storm horn",
        phrase="a tin storm horn mounted on a pole taller than the shed",
        raise_line="This horn will hear the sky before the sky hears itself",
        purpose="listen for giant weather music",
        top="the horn bell",
        material="tin pole",
        metal=True,
        sky_tall=True,
        spread=2,
        tags={"horn", "metal", "storm"},
    ),
    "spinner": Contraption(
        id="spinner",
        label="copper wind spinner",
        phrase="a copper wind spinner on a fishing pole long as a wagon",
        raise_line="This spinner will make the whole county hum",
        purpose="pull a humming song from the air",
        top="the spinner tip",
        material="copper stem",
        metal=True,
        sky_tall=True,
        spread=1,
        tags={"spinner", "metal", "storm"},
    ),
    "banner": Contraption(
        id="banner",
        label="cloth banner",
        phrase="a cloth banner on a willow stick",
        raise_line="This banner will wave the loudest hello in the county",
        purpose="dance with the wind",
        top="the banner tip",
        material="willow stick",
        metal=False,
        sky_tall=True,
        spread=0,
        tags={"banner"},
    ),
}

SAFE_TOOLS = {
    "drum": SafeTool(
        id="drum",
        label="porch drum",
        phrase="a porch drum made from an old flour barrel",
        action="boom out a proud tune from the ground",
        glow="made a deep happy sound without climbing a finger toward the clouds",
        tags={"drum", "music"},
    ),
    "pinwheel": SafeTool(
        id="pinwheel",
        label="paper pinwheel",
        phrase="a paper pinwheel painted with stars",
        action="whirl and sing right at hand",
        glow="spun bright as a candy wheel and stayed where feet could reach it",
        tags={"pinwheel", "wind"},
    ),
    "whistle": SafeTool(
        id="whistle",
        label="wooden whistle",
        phrase="a wooden whistle smooth as a river pebble",
        action="call out a clear tune from a safe little breath",
        glow="answered with a sweet note and no crackle at all",
        tags={"whistle", "music"},
    ),
}

RESPONSES = {
    "ground_chain": Response(
        id="ground_chain",
        sense=3,
        power=4,
        text="caught the {rig} with a dry rope, laid it flat, and clipped its line to the old ground chain by the porch post",
        fail="caught the {rig} with a dry rope and reached for the ground chain, but the charge had already skipped away",
        qa_text="lowered the contraption and grounded it with the old chain",
        tags={"ground", "storm"},
    ),
    "porch_hook": Response(
        id="porch_hook",
        sense=3,
        power=3,
        text="hooked the {rig} down with the porch crook and dragged it clear of the open hill before the charge could build any bigger",
        fail="hooked the {rig} down with the porch crook, but the spark jumped free first",
        qa_text="used the porch hook to pull the contraption down and away from the hilltop",
        tags={"ground", "storm"},
    ),
    "hat_swatter": Response(
        id="hat_swatter",
        sense=1,
        power=1,
        text="whacked at the spark with a broad hat until the crackle quit",
        fail="swatted with a broad hat, which bothered the spark no more than a moth bothers a barn door",
        qa_text="swatted at the spark with a hat",
        tags={"storm"},
    ),
}

GIRL_NAMES = ["June", "Maisie", "Dora", "Nell", "Pearl", "Willa", "Ruby", "Clara"]
BOY_NAMES = ["Hank", "Jeb", "Otis", "Beau", "Clyde", "Eli", "Wade", "Toby"]
TRAITS = ["careful", "thoughtful", "steady", "boastful", "stubborn", "showy"]
PETS = ["the hound", "the mule colt", "the yellow dog", "the barn cat"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for contraption_id, contraption in CONTRAPTIONS.items():
            if hazard_at_risk(place, contraption):
                combos.append((place_id, contraption_id))
    return combos


KNOWLEDGE = {
    "storm": [
        (
            "What does staticky mean in a storm?",
            "Staticky means the air is full of tiny crackly charges. It can make hair lift and can lead to sparks when the weather is building."
        )
    ],
    "ground": [
        (
            "What does it mean to ground something?",
            "To ground something means giving the extra charge a safe path into the earth instead of through people. That is why grown-ups lower and ground risky things during a storm."
        )
    ],
    "kite": [
        (
            "Why is a wire kite risky in stormy weather?",
            "A wire kite puts metal up high in the air, where storm charge can gather around it. That makes it a bad choice when clouds are crackling."
        )
    ],
    "horn": [
        (
            "Why is a tall metal horn risky in a storm?",
            "A tall metal horn reaches up toward the charged air. When storm clouds are building, that can invite dangerous sparks."
        )
    ],
    "spinner": [
        (
            "Why can a copper wind spinner be unsafe in a storm?",
            "Copper is metal, and a long spinner lifted high can collect storm charge. It is safer to keep metal things low and away from lightning weather."
        )
    ],
    "drum": [
        (
            "Why is a drum safer than lifting metal into a storm?",
            "A drum makes a big sound from the ground. It does not need to reach into a storm cloud to do its job."
        )
    ],
    "pinwheel": [
        (
            "Why is a paper pinwheel a safer windy-day toy?",
            "A paper pinwheel can spin in the breeze right at hand. It gives you wind fun without raising metal into dangerous weather."
        )
    ],
    "whistle": [
        (
            "Why is a wooden whistle a safer way to make sound?",
            "A wooden whistle works close to your face and hands, not high in the sky. It makes music without asking storm clouds to join in."
        )
    ],
}
KNOWLEDGE_ORDER = ["storm", "ground", "kite", "horn", "spinner", "drum", "pinwheel", "whistle"]


CURATED = [
    StoryParams(
        place="prairie",
        contraption="kite",
        safe_tool="drum",
        response="ground_chain",
        name="June",
        gender="girl",
        helper="grandpa",
        trait="boastful",
        delay=0,
        pet="the hound",
        boast="higher and higher",
    ),
    StoryParams(
        place="mesa",
        contraption="horn",
        safe_tool="whistle",
        response="porch_hook",
        name="Hank",
        gender="boy",
        helper="grandma",
        trait="showy",
        delay=1,
        pet="the yellow dog",
        boast="higher and higher",
    ),
    StoryParams(
        place="ridge",
        contraption="spinner",
        safe_tool="pinwheel",
        response="porch_hook",
        name="Pearl",
        gender="girl",
        helper="grandpa",
        trait="stubborn",
        delay=2,
        pet="the mule colt",
        boast="higher and higher",
    ),
    StoryParams(
        place="prairie",
        contraption="spinner",
        safe_tool="whistle",
        response="ground_chain",
        name="Eli",
        gender="boy",
        helper="grandma",
        trait="careful",
        delay=0,
        pet="",
        boast="higher and higher",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    contraption = f["contraption_cfg"]
    safe_tool = f["safe_tool_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the word "staticky" and the repeated phrase "higher and higher," but ends with a child listening to a warning before trouble starts.',
            f"Tell a tall tale about {child.id} on {place.label} with a {contraption.label}, where {helper.label_word} warns about the storm and the child learns the lesson in time.",
            f"Write a gentle tall tale where a boastful plan is repeated, then given up, and the ending uses {safe_tool.phrase} to prove the child learned something.",
        ]
    if outcome == "drained":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the word "staticky" and the repeated phrase "higher and higher," where a child raises something risky and a grown-up fixes the danger safely.',
            f"Tell a windy hill story where {child.id} ignores {helper.label_word}'s warning once, the air turns staticky, and the danger is stopped before anyone is hurt.",
            f"Write a tall tale with repetition, a lesson learned, and a safe ending image using {safe_tool.phrase}.",
        ]
    return [
        f'''Write a tall-tale story for a 3-to-5-year-old that includes the word "staticky" and the repeated phrase "higher and higher," where a child's bragging lets a storm make a messy warning mark.''',
        f"Tell a tall tale where {child.id} lifts a {contraption.label} into dangerous weather, a spark leaves a black stripe on something nearby, and the child learns to stop when the sky says no.",
        f"Write a cautionary but gentle story with repetition, a lesson learned, and a safe next-day ending using {safe_tool.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    contraption_cfg = f["contraption_cfg"]
    safe_tool = f["safe_tool_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    boast_line = f["boast"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, out on {place.label} with {contraption_cfg.phrase}. The story follows {child.id}'s wish to make the sky sound bigger than it should."
        ),
        (
            "What did the child keep saying?",
            f'{child.id} kept saying "{boast_line}" while lifting the contraption. The repetition shows how bragging kept pushing the choice in the wrong direction.'
        ),
        (
            f"Why did {helper.label_word} give a warning?",
            f'{helper.label_word.capitalize()} saw that the weather was turning staticky and knew the tall metal contraption did not belong in that sky. The warning came before the spark, because the danger was already building in the air.'
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed {child.id}'s mind?",
                f"{child.id} noticed the darkening sky and listened when {helper.label_word} explained what could happen. That choice stopped the trouble before a spark could begin."
            )
        )
    elif outcome == "drained":
        qa.append(
            (
                "What happened when the child lifted it again?",
                f"The air turned staticky, the contraption crackled, and {child.id}'s hair stood up. That happened because metal was held high just as the storm charge was gathering."
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} solve the problem?",
                f'{helper.label_word.capitalize()} {response.qa_text}. That worked because the risky thing was brought down and the charge was given a safer path away from the child.'
            )
        )
    else:
        qa.append(
            (
                "Did anyone get hurt when the spark jumped?",
                "No, nobody got hurt, but the spark left a warning mark on the old weather sign. That black stripe showed how quickly bragging could turn a silly plan into real trouble."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f'{child.id} learned not to keep chasing "higher and higher" when the sky is already saying no. The next-day safe play proves the lesson stuck instead of being forgotten.'
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The story ends with {safe_tool.phrase}, used under a calm sky. That ending image proves the child found a safer way to enjoy wind and sound."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["contraption_cfg"].tags) | set(f["safe_tool_cfg"].tags) | set(f["response"].tags)
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("metal", entity.metal),
            ("sky_tall", entity.sky_tall),
            ("grounded", entity.grounded),
            ("safe_sound", entity.safe_sound),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {entity.id:8} ({entity.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, contraption: Contraption) -> str:
    if not place.windy or place.surge < 1:
        return (
            f"(No story: {place.label} is too calm for a staticky storm tale, so the sky never becomes dangerous enough to turn {contraption.label} into a problem.)"
        )
    if not contraption.metal:
        return (
            f"(No story: {contraption.label} is not metal, so this world has no honest storm-static danger to warn about. Pick a metal contraption instead.)"
        )
    if not contraption.sky_tall:
        return (
            f"(No story: {contraption.label} does not reach high into the sky, so the warning would have no real cause.)"
        )
    return "(No story: this combination has no storm-static hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_averter(params.trait):
        return "averted"
    contained = is_drained(
        RESPONSES[params.response],
        PLACES[params.place],
        CONTRAPTIONS[params.contraption],
        params.delay,
    )
    return "drained" if contained else "scorched"


ASP_RULES = r"""
hazard(P,C) :- place(P), contraption(C), windy(P), surge(P,S), S >= 1, metal(C), sky_tall(C).
valid(P,C)  :- hazard(P,C).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.

humble(T)   :- trait(T), humble_trait(T).
averted     :- humble(T), trait(T).

severity(Su + Sp + D) :- chosen_place(P), surge(P,Su), chosen_contraption(C), spread(C,Sp), delay(D).
resp_power(Pw)        :- chosen_response(R), power(R,Pw).
drained               :- not averted, resp_power(Pw), severity(Se), Pw >= Se.

outcome(averted)  :- averted.
outcome(drained)  :- not averted, drained.
outcome(scorched) :- not averted, not drained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.windy:
            lines.append(asp.fact("windy", place_id))
        lines.append(asp.fact("surge", place_id, place.surge))
    for contraption_id, contraption in CONTRAPTIONS.items():
        lines.append(asp.fact("contraption", contraption_id))
        if contraption.metal:
            lines.append(asp.fact("metal", contraption_id))
        if contraption.sky_tall:
            lines.append(asp.fact("sky_tall", contraption_id))
        lines.append(asp.fact("spread", contraption_id, contraption.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(HUMBLE_TRAITS):
        lines.append(asp.fact("humble_trait", trait))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_contraption", params.contraption),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a stormy boast, and a staticky lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--contraption", choices=CONTRAPTIONS)
    ap.add_argument("--safe-tool", dest="safe_tool", choices=SAFE_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandma", "grandpa", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.contraption:
        place = PLACES[args.place]
        contraption = CONTRAPTIONS[args.contraption]
        if not hazard_at_risk(place, contraption):
            raise StoryError(explain_rejection(place, contraption))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.contraption is None or combo[1] == args.contraption)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, contraption_id = rng.choice(sorted(combos))
    safe_tool_id = args.safe_tool or rng.choice(sorted(SAFE_TOOLS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandma", "grandpa", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        place=place_id,
        contraption=contraption_id,
        safe_tool=safe_tool_id,
        response=response_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        delay=delay,
        pet=pet,
        boast="higher and higher",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.contraption not in CONTRAPTIONS:
        raise StoryError(f"(Unknown contraption: {params.contraption})")
    if params.safe_tool not in SAFE_TOOLS:
        raise StoryError(f"(Unknown safe tool: {params.safe_tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    contraption = CONTRAPTIONS[params.contraption]
    response = RESPONSES[params.response]
    if not hazard_at_risk(place, contraption):
        raise StoryError(explain_rejection(place, contraption))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        contraption=contraption,
        safe_tool=SAFE_TOOLS[params.safe_tool],
        response=response,
        name=params.name,
        gender=params.gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
        pet=params.pet,
        boast_line=params.boast,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, contraption) combos:\n")
        for place_id, contraption_id in combos:
            print(f"  {place_id:8} {contraption_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.contraption} on {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
