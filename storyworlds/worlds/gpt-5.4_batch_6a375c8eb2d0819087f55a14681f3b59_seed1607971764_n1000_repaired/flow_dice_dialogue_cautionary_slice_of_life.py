#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py
=========================================================================

A standalone story world about two children racing little boats in rainwater,
rolling dice to choose turns, and learning not to chase toys into gutter flow.

This world models a small slice-of-life cautionary story:
- a rainy-day game starts in an ordinary, cozy way
- one boat is pulled toward a drain by the flow
- one child wants to hurry after it
- another child warns them, and a grown-up helps in the sensible way
- afterward, the family finds a safer place to play the same game

Run it
------
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py --setting apartment_curb --drain storm_drain
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py --response bare_hand
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/flow_dice_dialogue_cautionary_slice_of_life.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "watchful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    open_gap: bool = False
    # physical and emotional dimensions
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
class Setting:
    id: str
    place: str
    opening: str
    home_line: str
    flow_strength: int
    street_edge: bool
    scene: str
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
class Boat:
    id: str
    label: str
    phrase: str
    material: str
    start_line: str
    drift_line: str
    plural: bool = False
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
class Drain:
    id: str
    label: str
    the: str
    swirl: str
    pull: int
    open_gap: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class SafePlay:
    id: str
    phrase: str
    place_line: str
    water_line: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["at_curb"] < THRESHOLD:
            continue
        sig = ("danger", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "water" in world.entities:
            world.get("water").meters["danger"] += 1
        for other in world.kids():
            other.memes["fear"] += 1
        out.append("__danger__")
    return out


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["stepped_in_runoff"] < THRESHOLD:
            sig = None
        else:
            sig = ("soak", kid.id)
        if not sig or sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["wet_shoe"] += 1
        kid.memes["shock"] += 1
        out.append(f"{kid.id}'s shoe splashed into the cold water.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="soak", tag="physical", apply=_r_soak),
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


def hazard_at_risk(setting: Setting, drain: Drain) -> bool:
    return setting.flow_strength > 0 and drain.open_gap


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def current_severity(setting: Setting, drain: Drain) -> int:
    return setting.flow_strength + drain.pull


def is_recovered(response: Response, setting: Setting, drain: Drain) -> bool:
    return response.power >= current_severity(setting, drain)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_chase(world: World) -> dict:
    sim = world.copy()
    runner = sim.get("instigator")
    runner.meters["at_curb"] += 1
    runner.meters["stepped_in_runoff"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("water").meters["danger"],
        "wet_shoe": runner.meters["wet_shoe"],
    }


def play_setup(world: World, a: Entity, b: Entity, setting: Setting, boat: Boat) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"After the rain, {a.id} and {b.id} stood by {setting.place}. {setting.scene}"
    )
    world.say(
        f"They had folded {boat.phrase}, and two small dice clicked in {a.id}'s palm "
        f"to choose whose turn would come first."
    )
    world.say(boat.start_line)


def launch(world: World, a: Entity, b: Entity, boat: Boat, setting: Setting) -> None:
    world.say(
        f'"Ready?" {a.id} asked. "{b.id}, you roll first."'
    )
    world.say(
        f'The dice bounced, {b.id} laughed, and together they set the little {boat.label} '
        f"into the thin gray flow beside the curb."
    )
    world.say(boat.drift_line)
    world.say(setting.opening)


def warn(world: World, b: Entity, a: Entity, drain: Drain, parent: Entity) -> None:
    pred = predict_chase(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_wet_shoe"] = pred["wet_shoe"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} took one quick step back from the edge."
    world.say(
        f'"Wait," {b.id} said. "Don\'t chase it there. {drain.The} is pulling it, '
        f'and {parent.label_word} said we stay back from fast water by the street."{extra}'
    )


def tempt(world: World, a: Entity, boat: Boat, drain: Drain) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"I can still get it," {a.id} said. "It\'s only {boat.phrase} near {drain.the}."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the rushing water, then at {b.id}, and stopped with "
        f"{a.pronoun('possessive')} toes still on the safe side of the curb."
    )
    world.say(
        f'"Okay," {a.pronoun()} whispered. "Let\'s tell {parent.label_word}."'
    )


def chase(world: World, a: Entity, drain: Drain) -> None:
    a.memes["defiance"] += 1
    a.meters["at_curb"] += 1
    a.meters["stepped_in_runoff"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {a.id} darted after the boat and stretched one foot toward {drain.the}.'
    )
    if a.meters["wet_shoe"] >= THRESHOLD:
        world.say(
            f"The water lapped over the edge of {a.pronoun('possessive')} shoe, cold and surprising."
        )


def call_parent(world: World, b: Entity, parent: Entity, drain: Drain) -> None:
    world.say(f'"{parent.label_word.upper()}! The boat is going to {drain.the}!" {b.id} called.')


def rescue(world: World, parent: Entity, response: Response, boat_ent: Entity, drain: Drain) -> None:
    boat_ent.meters["lost"] = 0.0
    boat_ent.meters["saved"] += 1
    if "water" in world.entities:
        world.get("water").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.text.replace('{drain}', drain.label)}."
    )
    world.say(
        f"In another moment, the little boat was safe again, dripping but still whole."
    )


def lose_boat(world: World, parent: Entity, response: Response, boat_ent: Entity, drain: Drain) -> None:
    boat_ent.meters["lost"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.fail.replace('{drain}', drain.label)}."
    )
    world.say(
        f"The boat spun once, slipped under the metal bars, and was gone."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, drain: Drain) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a second, all three of them listened to the water hiss along the edge of the street.")
    world.say(
        f'Then {parent.label_word} crouched beside them. "Boats can be replaced," '
        f'{parent.pronoun()} said softly. "You cannot. When water is moving fast toward '
        f'{drain.the}, children stop and call a grown-up."'
    )


def comfort(world: World, parent: Entity, a: Entity, b: Entity, recovered: bool) -> None:
    if recovered:
        world.say(
            f'{a.id} nodded and leaned into {parent.label_word} for one quick hug. '
            f'{b.id} touched the damp boat and let out a careful little breath.'
        )
    else:
        a.memes["sad"] += 1
        b.memes["sad"] += 1
        world.say(
            f'{a.id} blinked hard at the empty grate, and {b.id} slipped a hand into '
            f'{a.pronoun("possessive")} hand. They were safe, even though the game piece was gone.'
        )


def safe_after(world: World, parent: Entity, a: Entity, b: Entity, safe_play: SafePlay, boat: Boat) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.para()
    world.say(
        f"Later that afternoon, {parent.label_word} carried {safe_play.phrase} to {safe_play.place_line}."
    )
    world.say(
        f"{safe_play.water_line} The children rolled the dice again and set the little {boat.label} down where no drain could steal it."
    )
    world.say(
        f"This time they watched the boat drift, counted the turns out loud, and kept both feet warm and dry."
    )


def tell(
    setting: Setting,
    boat: Boat,
    drain: Drain,
    response: Response,
    safe_play: SafePlay,
    *,
    instigator: str = "Ben",
    instigator_gender: str = "boy",
    cautioner: str = "Mia",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            age=instigator_age,
            traits=["eager"],
            attrs={"name": instigator, "relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"name": cautioner, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            attrs={"name": "Parent"},
        )
    )
    water = world.add(Entity(id="water", type="runoff", label="rainwater"))
    boat_ent = world.add(Entity(id="boat", type="boat", label=boat.label))
    drain_ent = world.add(Entity(id="drain", type="drain", label=drain.label, open_gap=drain.open_gap))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    water.meters["flow"] = float(setting.flow_strength)
    drain_ent.meters["pull"] = float(drain.pull)

    play_setup(world, a, b, setting, boat)
    launch(world, a, b, boat, setting)

    world.para()
    warn(world, b, a, drain, parent)
    tempt(world, a, boat, drain)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        lesson(world, parent, a, b, drain)
        recovered = True
    else:
        chase(world, a, drain)
        call_parent(world, b, parent, drain)
        world.para()
        recovered = is_recovered(response, setting, drain)
        if recovered:
            rescue(world, parent, response, boat_ent, drain)
        else:
            lose_boat(world, parent, response, boat_ent, drain)
        lesson(world, parent, a, b, drain)
        comfort(world, parent, a, b, recovered)

    safe_after(world, parent, a, b, safe_play, boat)

    outcome = "averted" if averted else ("recovered" if recovered else "lost")
    world.facts.update(
        setting=setting,
        boat_cfg=boat,
        drain_cfg=drain,
        response=response,
        safe_play=safe_play,
        instigator=a,
        cautioner=b,
        parent=parent,
        boat=boat_ent,
        drain=drain_ent,
        outcome=outcome,
        relation=relation,
        recovered=recovered,
        averted=averted,
        severity=current_severity(setting, drain),
    )
    return world


SETTINGS = {
    "apartment_curb": Setting(
        id="apartment_curb",
        place="the front curb outside their apartment",
        opening="A skinny stripe of rainwater hurried along the gutter, and ahead of it waited a square storm opening in the curb.",
        home_line="the covered front step",
        flow_strength=2,
        street_edge=True,
        scene="The clouds had already broken apart, but the gutter still carried a quick silver flow.",
        tags={"rain", "gutter", "street"},
    ),
    "park_path": Setting(
        id="park_path",
        place="the path beside the park fence",
        opening="Water from the hill ran beside the path in a shining ribbon, straight toward a drain grate near the corner.",
        home_line="a bench under the park shelter",
        flow_strength=1,
        street_edge=False,
        scene="Wet leaves clung to the fence, and the path gleamed after the shower.",
        tags={"rain", "park", "drain"},
    ),
    "school_gate": Setting(
        id="school_gate",
        place="the sidewalk near the school gate",
        opening="The water slid in a narrow line beside the curb and tugged everything toward the grated mouth at the corner.",
        home_line="the awning by the gate",
        flow_strength=2,
        street_edge=True,
        scene="Backpacks leaned against the wall while the last drops fell from the metal gate.",
        tags={"rain", "street", "school"},
    ),
}

BOATS = {
    "paper": Boat(
        id="paper",
        label="paper boat",
        phrase="a little paper boat",
        material="paper",
        start_line="One boat had a blue stripe across the sail, and both children bent close as if it were something important.",
        drift_line="For a few bright seconds it floated beautifully, tipping and righting itself as the water found its way.",
        tags={"paper_boat"},
    ),
    "leaf": Boat(
        id="leaf",
        label="leaf boat",
        phrase="a leaf boat with a toothpick mast",
        material="leaf",
        start_line="Its green sides looked brave and wobbly at the same time.",
        drift_line="It skimmed the surface lightly and turned wherever the water told it to turn.",
        tags={"leaf_boat"},
    ),
    "foil": Boat(
        id="foil",
        label="foil boat",
        phrase="a small foil boat",
        material="foil",
        start_line="It flashed when the light touched it, as if it had made itself from kitchen treasure.",
        drift_line="It slid faster than they expected and shivered whenever the water bumped the curb.",
        tags={"foil_boat"},
    ),
}

DRAINS = {
    "storm_drain": Drain(
        id="storm_drain",
        label="storm drain",
        the="the storm drain",
        swirl="the water circled hard over the bars",
        pull=2,
        open_gap=True,
        tags={"storm_drain", "fast_water"},
    ),
    "corner_grate": Drain(
        id="corner_grate",
        label="corner grate",
        the="the corner grate",
        swirl="the water curled through the grate in a tight little whirl",
        pull=1,
        open_gap=True,
        tags={"drain", "fast_water"},
    ),
    "flowerbed": Drain(
        id="flowerbed",
        label="flowerbed",
        the="the flowerbed",
        swirl="the water simply soaked into the dirt",
        pull=0,
        open_gap=False,
        tags={"garden"},
    ),
}

RESPONSES = {
    "umbrella_hook": Response(
        id="umbrella_hook",
        sense=3,
        power=4,
        text="used the hooked handle of a closed umbrella to catch the boat before it reached the {drain}",
        fail="reached with the hooked umbrella, but the current whisked the boat past the {drain} too quickly",
        qa_text="used a closed umbrella hook to catch the boat before the drain took it",
        tags={"umbrella", "retrieval"},
    ),
    "kitchen_tongs": Response(
        id="kitchen_tongs",
        sense=3,
        power=2,
        text="knelt from the safe side and pinched the boat out of the water with long kitchen tongs",
        fail="tried to pinch the boat with kitchen tongs, but it slipped away toward the drain",
        qa_text="used long kitchen tongs from the safe side to lift the boat out",
        tags={"tongs", "retrieval"},
    ),
    "let_go": Response(
        id="let_go",
        sense=2,
        power=0,
        text="did not chase the boat at all",
        fail="kept everyone back and let the boat go",
        qa_text="kept the children back and let the boat go",
        tags={"let_go", "safety"},
    ),
    "bare_hand": Response(
        id="bare_hand",
        sense=1,
        power=1,
        text="reached into the runoff with a bare hand and snatched the boat out",
        fail="reached with a bare hand, but the boat slid away faster than fingers could catch it",
        qa_text="reached in with a bare hand",
        tags={"unsafe"},
    ),
}

SAFE_PLAYS = {
    "wash_tub": SafePlay(
        id="wash_tub",
        phrase="a shallow wash tub",
        place_line="the covered front step",
        water_line="Parent poured in just enough water to make a gentle pretend river.",
        tags={"safe_water", "tub"},
    ),
    "baking_tray": SafePlay(
        id="baking_tray",
        phrase="an old baking tray",
        place_line="the kitchen table by the window",
        water_line="A thin sheet of water made a tiny channel without any rushing edge at all.",
        tags={"safe_water", "tray"},
    ),
    "plastic_basin": SafePlay(
        id="plastic_basin",
        phrase="a blue plastic basin",
        place_line="the laundry-room floor",
        water_line="The water sat still until they pushed their boats with one finger and made their own slow flow.",
        tags={"safe_water", "basin", "flow"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Theo", "Noah", "Sam", "Leo", "Eli", "Finn"]
TRAITS = ["careful", "steady", "thoughtful", "watchful", "gentle", "quietly brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id, setting in SETTINGS.items():
        for boat_id in BOATS:
            for drain_id, drain in DRAINS.items():
                if hazard_at_risk(setting, drain):
                    combos.append((setting_id, boat_id, drain_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    boat: str
    drain: str
    response: str
    safe_play: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "dice": [
        (
            "What are dice?",
            "Dice are small cubes used in games. You roll them to get numbers and decide turns or moves."
        )
    ],
    "flow": [
        (
            "What does flow mean when water is moving?",
            "Flow means the way water moves from one place to another. Fast flow can tug light things along before you can grab them."
        )
    ],
    "storm_drain": [
        (
            "What is a storm drain for?",
            "A storm drain carries rainwater away from streets and sidewalks. It is not a place for children to reach into or play near."
        )
    ],
    "drain": [
        (
            "Why can a drain take a toy away?",
            "Moving water pulls light things toward the opening. Once a toy slips through the bars, it is hard to get back."
        )
    ],
    "gutter": [
        (
            "What is a gutter by the curb?",
            "The gutter is the low edge beside the street where rainwater runs. It can look small, but the water there can still move quickly."
        )
    ],
    "umbrella": [
        (
            "Why is a closed umbrella safer than a hand for reaching a floating toy?",
            "A closed umbrella lets a grown-up reach from farther back. That means hands and feet can stay away from the rushing water."
        )
    ],
    "tongs": [
        (
            "What are kitchen tongs?",
            "Kitchen tongs are long tools for picking things up without using your fingers. A grown-up can use them to reach something while staying back."
        )
    ],
    "paper_boat": [
        (
            "Why does a paper boat move on water?",
            "Water pushes lightly against the boat and carries it along. If the flow is quick, the boat can travel faster than you expect."
        )
    ],
    "safe_water": [
        (
            "Why is a tub or tray safer for boat play than a street drain?",
            "A tub or tray keeps the water close and gentle. There is no street edge and no drain to swallow the boats."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "dice",
    "flow",
    "storm_drain",
    "drain",
    "gutter",
    "umbrella",
    "tongs",
    "paper_boat",
    "safe_water",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    setting = f["setting"]
    boat = f["boat_cfg"]
    drain = f["drain_cfg"]
    safe_play = f["safe_play"]
    outcome = f["outcome"]
    base = (
        f'Write a short slice-of-life cautionary story for a 3-to-5-year-old that includes the words "flow" and "dice". '
        f'Two children race {boat.label}s in rainwater near {drain.the}, and the story is told mostly through dialogue.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle rainy-day story where {a.label} wants to chase a boat toward {drain.the}, but {b.label} warns {a.pronoun('object')} in time and they call a grown-up instead.",
            f"Write a simple family story where children use dice to choose turns, almost make an unsafe choice near street water, and then move their game to {safe_play.phrase}.",
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a cautionary story where {a.label} dashes after a boat, but the grown-up keeps the children safe even though the boat is lost in {drain.the}.",
            f"Write a dialogue-rich story where the lesson is that toys can be replaced, but children must stay back from fast water and drains.",
        ]
    return [
        base,
        f"Tell a rainy slice-of-life story where {a.label} chases a floating boat, {b.label} calls for help, and a calm grown-up rescues the boat safely.",
        f"Write a cautionary but comforting story that ends with the children still playing their boat-and-dice game in {safe_play.phrase} instead of near the street.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    setting = f["setting"]
    boat = f["boat_cfg"]
    drain = f["drain_cfg"]
    response = f["response"]
    safe_play = f["safe_play"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, playing with a little boat after the rain. Their {pw} helps when the game starts to feel unsafe."
        ),
        (
            "Why were the children rolling dice?",
            f"They were using the dice to choose turns for their boat race. The clicking dice made the game feel playful before the trouble began."
        ),
        (
            f"Why did {b.label} tell {a.label} to stop?",
            f"{b.label} saw that the boat was being pulled by the flow toward {drain.the}. {b.pronoun().capitalize()} knew chasing it would put {a.label} too close to fast water at the edge."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.label} do after the warning?",
                f"{a.label} stopped before stepping off the safe side of the curb and called for {pw}'s help instead. That choice kept the game from turning into a bigger scare."
            )
        )
    elif f["outcome"] == "recovered":
        qa.append(
            (
                f"How did {pw} save the boat?",
                f"{pw.capitalize()} {response.qa_text.replace('{drain}', drain.label)}. The grown-up could help safely from farther back, which is why the boat was rescued without anyone leaning into the water."
            )
        )
    else:
        qa.append(
            (
                "Did they get the boat back?",
                f"No. The boat slipped into {drain.the} and was lost. Even so, the grown-up kept the children back, and staying safe mattered more than saving the toy."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the family moving the game to {safe_play.phrase}. The children rolled the dice again there, which showed they had learned a safer way to keep playing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"dice", "flow", "safe_water"}
    setting = world.facts["setting"]
    drain = world.facts["drain_cfg"]
    boat = world.facts["boat_cfg"]
    response = world.facts["response"]

    tags |= set(setting.tags)
    tags |= set(drain.tags)
    tags |= set(boat.tags)
    tags |= set(response.tags)

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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.open_gap:
            bits.append("open_gap=True")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment_curb",
        boat="paper",
        drain="storm_drain",
        response="umbrella_hook",
        safe_play="wash_tub",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="park_path",
        boat="leaf",
        drain="corner_grate",
        response="kitchen_tongs",
        safe_play="baking_tray",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Noah",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        setting="school_gate",
        boat="foil",
        drain="storm_drain",
        response="let_go",
        safe_play="plastic_basin",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
]


def explain_rejection(setting: Setting, drain: Drain) -> str:
    if not drain.open_gap:
        return (
            f"(No story: {setting.place} has moving water, but {drain.the} is not an open drain that can take the boat away. "
            f"Without a real pull toward a gap, there is no honest cautionary turn.)"
        )
    return "(No story: this setting and drain do not make a real retrieval risk.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too low-sense for this storyworld "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    recovered = is_recovered(RESPONSES[params.response], SETTINGS[params.setting], DRAINS[params.drain])
    return "recovered" if recovered else "lost"


ASP_RULES = r"""
hazard(S, D) :- setting(S), drain(D), flow_strength(S, F), F > 0, open_gap(D).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, B, D) :- setting(S), boat(B), drain(D), hazard(S, D).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(F + P) :- chosen_setting(S), chosen_drain(D), flow_strength(S, F), pull(D, P).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
recovered :- not averted, resp_power(Pw), severity(V), Pw >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("flow_strength", sid, setting.flow_strength))
    for bid in BOATS:
        lines.append(asp.fact("boat", bid))
    for did, drain in DRAINS.items():
        lines.append(asp.fact("drain", did))
        if drain.open_gap:
            lines.append(asp.fact("open_gap", did))
        lines.append(asp.fact("pull", did, drain.pull))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_drain", params.drain),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    py_sense = {r.id for r in sensible_responses()}
    clingo_sense = set(asp_sensible())
    if py_sense == clingo_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(py_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: rainy-day boat racing with dice, moving water, and a safer second try."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--drain", choices=DRAINS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--safe-play", dest="safe_play", choices=SAFE_PLAYS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drain:
        drain = DRAINS[args.drain]
        if not drain.open_gap:
            setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
            raise StoryError(explain_rejection(setting, drain))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.boat is None or combo[1] == args.boat)
        and (args.drain is None or combo[2] == args.drain)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, boat_id, drain_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_play_id = args.safe_play or rng.choice(sorted(SAFE_PLAYS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        setting=setting_id,
        boat=boat_id,
        drain=drain_id,
        response=response_id,
        safe_play=safe_play_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.boat not in BOATS:
        raise StoryError(f"(Unknown boat: {params.boat})")
    if params.drain not in DRAINS:
        raise StoryError(f"(Unknown drain: {params.drain})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.safe_play not in SAFE_PLAYS:
        raise StoryError(f"(Unknown safe play: {params.safe_play})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(SETTINGS[params.setting], DRAINS[params.drain]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], DRAINS[params.drain]))

    world = tell(
        SETTINGS[params.setting],
        BOATS[params.boat],
        DRAINS[params.drain],
        RESPONSES[params.response],
        SAFE_PLAYS[params.safe_play],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, boat, drain) combos:\n")
        for setting_id, boat_id, drain_id in combos:
            print(f"  {setting_id:15} {boat_id:8} {drain_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.boat} at {p.setting} near {p.drain} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
