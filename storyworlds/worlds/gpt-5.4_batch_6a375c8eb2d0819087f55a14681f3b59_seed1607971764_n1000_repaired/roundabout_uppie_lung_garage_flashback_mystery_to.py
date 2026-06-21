#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py
================================================================================

A standalone storyworld for a small, child-facing tall tale set in a garage:
a child and a kindly helper are getting a parade ride ready when a lucky
keepsake vanishes and a booming mystery sound fills the garage. The story
always includes a flashback, a mystery to solve, and the words "roundabout",
"uppie", and "lung" in natural prose.

This world models a few kinds of garage hideouts for the missing object and a
few search aids. It refuses invalid choices where the chosen aid could not
honestly solve the mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py
    python storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py --hideout wheel_hub --aid magnet_wand
    python storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py --hideout high_shelf_jar --aid flashlight
    python storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/roundabout_uppie_lung_garage_flashback_mystery_to.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "grandmother"}
        male = {"boy", "father", "uncle", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
            "uncle": "uncle",
            "aunt": "aunt",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Ride:
    id: str
    label: str
    phrase: str
    boast: str
    spin_text: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    shine: str
    luck_text: str
    material: str = "metal"
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
class Hideout:
    id: str
    label: str
    phrase: str
    kind: str
    noise_text: str
    clue_text: str
    flashback_text: str
    ending_place: str
    dark: bool = False
    high: bool = False
    narrow: bool = False
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
class Aid:
    id: str
    label: str
    phrase: str
    find_text: str
    reach_high: bool = False
    pull_metal: bool = False
    see_dark: bool = False
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


def _r_wheel_noise(world: World) -> list[str]:
    ride = world.entities.get("ride")
    keepsake = world.entities.get("keepsake")
    garage = world.entities.get("garage")
    if not ride or not keepsake or not garage:
        return []
    if keepsake.attrs.get("hideout") != "wheel_hub":
        return []
    if ride.meters["rolled"] < THRESHOLD:
        return []
    sig = ("wheel_noise", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    garage.meters["noise"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["worry"] += 1
            ent.memes["wonder"] += 1
    world.facts["noise_source"] = "wheel_hub"
    return ["__noise__"]


def _r_shelf_noise(world: World) -> list[str]:
    door = world.entities.get("door")
    keepsake = world.entities.get("keepsake")
    garage = world.entities.get("garage")
    if not door or not keepsake or not garage:
        return []
    if keepsake.attrs.get("hideout") != "high_shelf_jar":
        return []
    if door.meters["rattled"] < THRESHOLD:
        return []
    sig = ("shelf_noise", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    garage.meters["noise"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["worry"] += 1
            ent.memes["wonder"] += 1
    world.facts["noise_source"] = "high_shelf_jar"
    return ["__noise__"]


def _r_crack_noise(world: World) -> list[str]:
    door = world.entities.get("door")
    keepsake = world.entities.get("keepsake")
    garage = world.entities.get("garage")
    if not door or not keepsake or not garage:
        return []
    if keepsake.attrs.get("hideout") != "floor_crack":
        return []
    if door.meters["opened"] < THRESHOLD:
        return []
    sig = ("crack_noise", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    garage.meters["noise"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["worry"] += 1
            ent.memes["wonder"] += 1
    world.facts["noise_source"] = "floor_crack"
    return ["__noise__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wheel_noise", tag="physical", apply=_r_wheel_noise),
    Rule(name="shelf_noise", tag="physical", apply=_r_shelf_noise),
    Rule(name="crack_noise", tag="physical", apply=_r_crack_noise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def aid_fits(hideout: Hideout, aid: Aid, keepsake: Keepsake) -> bool:
    if keepsake.material != "metal":
        return False
    if hideout.kind == "shelf":
        return aid.reach_high
    if hideout.kind in {"wheel", "crack"}:
        return aid.pull_metal
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for ride_id in RIDES:
        for keepsake_id, keepsake in KEEPSAKES.items():
            for hideout_id, hideout in HIDEOUTS.items():
                for aid_id, aid in AIDS.items():
                    if aid_fits(hideout, aid, keepsake):
                        combos.append((ride_id, keepsake_id, hideout_id, aid_id))
    return combos


def predict_noise(world: World) -> dict:
    sim = world.copy()
    ride = sim.get("ride")
    door = sim.get("door")
    hideout = sim.facts["hideout_cfg"]
    if hideout.id == "wheel_hub":
        ride.meters["rolled"] += 1
    elif hideout.id == "high_shelf_jar":
        door.meters["rattled"] += 1
    else:
        door.meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("garage").meters["noise"],
        "source": sim.facts.get("noise_source", ""),
    }


def introduce(world: World, child: Entity, helper: Entity, ride: Ride, keepsake: Keepsake) -> None:
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"In the garage, {child.id} and {helper.label_word} were getting {ride.phrase} ready "
        f"for the Saturday parade. It looked so grand that even the lawn mower seemed to stand "
        f"up straighter to salute it."
    )
    world.say(
        f"{child.id} loved one thing best of all: {keepsake.phrase}, {keepsake.shine}. "
        f"{keepsake.luck_text}"
    )
    world.say(
        f'{helper.label_word.capitalize()} said the ride was not merely nice. "{ride.boast}," '
        f"{helper.pronoun()} declared, and {child.id} believed every splendid word."
    )


def setup_missing(world: World, child: Entity, helper: Entity, ride: Ride, keepsake: Keepsake) -> None:
    world.say(
        f"When {child.id} reached for {keepsake.label}, though, the lucky piece was gone. "
        f"The handlebar was bare, the workbench was bare, and the whole garage suddenly felt "
        f"full of questions."
    )
    child.memes["worry"] += 1
    world.say(
        f'"Where did it go?" {child.id} whispered. {helper.label_word.capitalize()} tipped '
        f"{helper.pronoun('possessive')} head. A missing keepsake before a parade was a mystery "
        f"big enough to make a toolbox seem deep as a canyon."
    )


def stir_mystery(world: World, child: Entity, helper: Entity, hideout: Hideout, ride: Ride) -> None:
    pred = predict_noise(world)
    world.facts["predicted_noise"] = pred["noise"]
    if hideout.id == "wheel_hub":
        world.get("ride").meters["rolled"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Just then {helper.label_word} gave {ride.label} a little shove. "
            f"{hideout.noise_text} The sound went roundabout the garage walls as if it had "
            f"borrowed a hundred tin boots."
        )
    elif hideout.id == "high_shelf_jar":
        world.get("door").meters["rattled"] += 1
        propagate(world, narrate=False)
        world.say(
            f"A breeze nudged the garage door, and {hideout.noise_text} The sound ran roundabout "
            f"the rafters and came back twice as large."
        )
    else:
        world.get("door").meters["opened"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{helper.label_word.capitalize()} cracked the side door for light, and {hideout.noise_text} "
            f"It slipped in a roundabout curl past their ankles."
        )
    world.say(
        f"{child.id} filled each lung like a little brave balloon. "
        f'"That noise knows something," {child.pronoun()} said.'
    )
    child.memes["wonder"] += 1


def investigate(world: World, child: Entity, helper: Entity, hideout: Hideout, aid: Aid, keepsake: Keepsake) -> None:
    child.memes["focus"] += 1
    world.say(
        f'{helper.label_word.capitalize()} fetched {aid.phrase}. "{aid.find_text}," '
        f"{helper.pronoun()} said. Together they listened, looked, and moved slowly enough "
        f"for clues to stop hiding."
    )
    world.say(hideout.clue_text)
    world.facts["clue_found"] = True
    child.memes["hope"] += 1


def flashback(world: World, child: Entity, helper: Entity, hideout: Hideout) -> None:
    child.memes["memory"] += 1
    world.para()
    world.say(
        f"Then a bright little flashback popped into {child.id}'s mind. "
        f"{hideout.flashback_text}"
    )
    world.say(
        f'That was it. "{helper.label_word.capitalize()}, I remember!" {child.id} cried. '
        f"The old moment and the new noise clicked together like two puzzle pieces."
    )


def recover(world: World, child: Entity, helper: Entity, hideout: Hideout, aid: Aid, keepsake: Keepsake) -> None:
    k = world.get("keepsake")
    k.attrs["found_in"] = hideout.id
    k.attrs["hideout"] = ""
    k.meters["lost"] = 0.0
    k.meters["found"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    if hideout.id == "high_shelf_jar":
        world.say(
            f"{helper.label_word.capitalize()} climbed carefully, reached into the jar, "
            f"and lifted out {keepsake.label}. It flashed once, small and proud, as if it "
            f"had been waiting to be discovered by true detectives."
        )
    else:
        world.say(
            f"{helper.label_word.capitalize()} swept {aid.label} toward the hiding place, and "
            f"{keepsake.label} came skimming out with a cheerful little cling. The mystery had "
            f"lost its last secret."
        )
    world.facts["recovered"] = True


def ending(world: World, child: Entity, helper: Entity, keepsake: Keepsake, hideout: Hideout, ride: Ride) -> None:
    child.memes["safety"] += 1
    world.say(
        f'"No more loose luck in a busy garage," {helper.label_word} said. This time they set '
        f"{keepsake.label} in {hideout.ending_place} until parade time."
    )
    world.say(
        f"When they finally pinned it back onto {ride.label}, the garage seemed to smile all at once. "
        f"{child.id} patted the shiny piece, and the ride waited as grand and still as a mountain "
        f"that had decided to roll only for parades."
    )
    world.say(
        f"After that, whenever the garage muttered and clanked, {child.id} did not feel small. "
        f"{child.pronoun().capitalize()} took a steady breath, remembered the flashback, and listened for the truth."
    )


def tell(
    ride: Ride,
    keepsake: Keepsake,
    hideout: Hideout,
    aid: Aid,
    child_name: str = "Poppy",
    child_gender: str = "girl",
    helper_name: str = "Grandpa Reed",
    helper_type: str = "grandfather",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["brave", "curious"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["kind", "handy"],
        attrs={},
    ))
    garage = world.add(Entity(
        id="garage",
        kind="thing",
        type="garage",
        label="the garage",
        phrase="the garage",
        attrs={},
    ))
    door = world.add(Entity(
        id="door",
        kind="thing",
        type="garage_door",
        label="garage door",
        attrs={},
    ))
    ride_ent = world.add(Entity(
        id="ride",
        kind="thing",
        type="ride",
        label=ride.label,
        phrase=ride.phrase,
        attrs={"ride_id": ride.id},
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        attrs={"hideout": hideout.id, "found_in": ""},
    ))
    _ = garage, ride_ent, keepsake_ent  # silence lint-like tools

    world.facts.update(
        ride_cfg=ride,
        keepsake_cfg=keepsake,
        hideout_cfg=hideout,
        aid_cfg=aid,
        child=child,
        helper=helper,
        clue_found=False,
        recovered=False,
        predicted_noise=0,
    )

    introduce(world, child, helper, ride, keepsake)
    setup_missing(world, child, helper, ride, keepsake)

    world.para()
    stir_mystery(world, child, helper, hideout, ride)
    investigate(world, child, helper, hideout, aid, keepsake)

    flashback(world, child, helper, hideout)

    world.para()
    recover(world, child, helper, hideout, aid, keepsake)
    ending(world, child, helper, keepsake, hideout, ride)
    return world


RIDES = {
    "wagon": Ride(
        id="wagon",
        label="the parade wagon",
        phrase="a red parade wagon",
        boast="This wagon is so fine it could pull the moon to breakfast",
        spin_text="rolled its wheels in a proud red blur",
        tags={"wagon", "garage"},
    ),
    "scooter": Ride(
        id="scooter",
        label="the parade scooter",
        phrase="a blue parade scooter",
        boast="This scooter is so swift it could outrun a yawn",
        spin_text="twirled its front wheel like a happy coin",
        tags={"scooter", "garage"},
    ),
    "soapbox": Ride(
        id="soapbox",
        label="the soapbox racer",
        phrase="a silver soapbox racer",
        boast="This racer is so noble it would tip its hat to thunder",
        spin_text="sent its wheel humming like a bee with medals",
        tags={"soapbox", "garage"},
    ),
}

KEEPSAKES = {
    "bell": Keepsake(
        id="bell",
        label="the brass bell",
        phrase="a brass bell polished bright as honey",
        shine="with a golden blink in every curve",
        luck_text="Everyone said it made a ride sound lucky before it even moved",
        material="metal",
        tags={"bell", "metal"},
    ),
    "star": Keepsake(
        id="star",
        label="the silver star",
        phrase="a silver star medal",
        shine="with five sharp points ready to catch every crumb of light",
        luck_text="In parade stories, a star like that was supposed to point the way to good days",
        material="metal",
        tags={"star", "metal"},
    ),
    "whistle": Keepsake(
        id="whistle",
        label="the tin whistle",
        phrase="a tin whistle tied with red string",
        shine="with a trim little gleam along its side",
        luck_text="They liked to say it could call good luck faster than geese call one another",
        material="metal",
        tags={"whistle", "metal"},
    ),
}

HIDEOUTS = {
    "wheel_hub": Hideout(
        id="wheel_hub",
        label="the wheel hub",
        phrase="the hollow hub of the front wheel",
        kind="wheel",
        noise_text="Clink-clank-clink! Something tiny was dancing inside the wheel",
        clue_text="Near the front wheel they spotted a bright scratch and a thread of parade ribbon caught by the hub.",
        flashback_text='That morning, while tying streamers, '
                       f'{ "Grandpa" } had grinned and asked, "Need an uppie?" '
                       "Up she went, high enough to pat the handle and admire the wheel. "
                       "She had given the wheel one proud spin just to watch the ribbons fly.",
        ending_place="a small tin on the workbench with a lid that clicked shut",
        dark=False,
        high=False,
        narrow=True,
        tags={"wheel", "garage"},
    ),
    "high_shelf_jar": Hideout(
        id="high_shelf_jar",
        label="the high shelf jar",
        phrase="a jar of spare bolts on the highest shelf",
        kind="shelf",
        noise_text="Ping-ping! A tiny metal voice answered from high above",
        clue_text="On the top shelf, one bolt jar sat crooked, and inside the glass something flashed once like a trapped wink.",
        flashback_text='A little while before, '
                       f'{ "Grandpa" } had laughed, "Need an uppie?" '
                       "He had lifted her to set the lucky piece beside the paint jars 'just for one safe minute.' "
                       "Then the phone rang, and they both forgot.",
        ending_place="a labeled parade box on a middle shelf where small hands could still see it",
        dark=True,
        high=True,
        narrow=False,
        tags={"shelf", "garage"},
    ),
    "floor_crack": Hideout(
        id="floor_crack",
        label="the floor crack",
        phrase="a skinny crack in the garage floor",
        kind="crack",
        noise_text="Whee-eee! A thin secret whistled from the floor",
        clue_text="By the door lay a curl of red string, and the dust there had been rubbed shiny in one narrow line.",
        flashback_text='Earlier, while hanging the parade banner, '
                       f'{ "Grandpa" } had asked, "Need an uppie?" '
                       "From up high she had kicked her heels with delight, and something small must have bounced free when they came down.",
        ending_place="a sturdy hook by the workbench instead of near the busy floor",
        dark=True,
        high=False,
        narrow=True,
        tags={"crack", "garage"},
    ),
}

AIDS = {
    "magnet_wand": Aid(
        id="magnet_wand",
        label="the magnet wand",
        phrase="a magnet wand with a blue handle",
        find_text="Metal likes to tell the truth when a magnet comes calling",
        reach_high=False,
        pull_metal=True,
        see_dark=False,
        tags={"magnet", "metal"},
    ),
    "step_stool": Aid(
        id="step_stool",
        label="the step stool",
        phrase="a trusty step stool with paint freckles on its legs",
        find_text="A high clue is still a clue, if we rise to meet it",
        reach_high=True,
        pull_metal=False,
        see_dark=False,
        tags={"stool", "high"},
    ),
    "flashlight": Aid(
        id="flashlight",
        label="the flashlight",
        phrase="a flashlight bright as a pocket moon",
        find_text="Light helps us see, even when it cannot reach with fingers",
        reach_high=False,
        pull_metal=False,
        see_dark=True,
        tags={"flashlight", "light"},
    ),
}

GIRL_NAMES = ["Poppy", "Mira", "Lucy", "Nora", "Ada", "June"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Owen", "Max", "Ben"]
HELPERS = {
    "grandfather": ["Grandpa Reed", "Grandpa Moss", "Grandpa Hale"],
    "grandmother": ["Grandma June", "Grandma Tess", "Grandma Rue"],
    "uncle": ["Uncle Ben", "Uncle Theo", "Uncle Miles"],
    "aunt": ["Aunt May", "Aunt Wren", "Aunt June"],
}


@dataclass
class StoryParams:
    ride: str
    keepsake: str
    hideout: str
    aid: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
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
    "garage": [
        (
            "What is a garage?",
            "A garage is a place next to a house where people keep things like bikes, tools, or a car. It can be a busy place, so small special things are safer when they are put away carefully.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some kinds of metal toward it without touching first. That makes it useful for finding small metal things in tight places.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps a person reach something that is too high. It should be used carefully on a steady floor.",
        )
    ],
    "lung": [
        (
            "What do lungs do?",
            "Lungs help your body breathe by taking air in and letting air out. A slow breath can help you feel calm enough to think.",
        )
    ],
    "bell": [
        (
            "Why does a metal bell make a ringing sound?",
            "When a bell bumps or shakes, the metal vibrates very quickly. That fast shaking makes a clear ringing sound.",
        )
    ],
    "wheel": [
        (
            "Why can something hidden in a wheel make noise?",
            "If a small object gets stuck in a wheel, it can tap and rattle each time the wheel turns. The spinning keeps bumping it around again and again.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short part that remembers something from earlier. It helps explain what is happening now.",
        )
    ],
}
KNOWLEDGE_ORDER = ["garage", "magnet", "stool", "lung", "bell", "wheel", "flashback"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ride = f["ride_cfg"]
    keepsake = f["keepsake_cfg"]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old set in a garage where a child must solve a mystery and a flashback helps explain it. Include the words "roundabout", "uppie", and "lung".',
        f"Tell a child-facing mystery about {child.id} and {helper.label_word} getting {ride.label} ready when {keepsake.label} goes missing and a strange garage noise gives the first clue.",
        f"Write a warm, exaggerated story where a missing lucky object is found by careful thinking instead of panic, and the ending shows a safer new place for it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ride = f["ride_cfg"]
    keepsake = f["keepsake_cfg"]
    hideout = f["hideout_cfg"]
    aid = f["aid_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, who were getting {ride.label} ready in the garage. They had to solve the mystery of the missing {keepsake.label}.",
        ),
        (
            f"What was the mystery?",
            f"The lucky {keepsake.label} was gone, and a strange sound started up in the garage. The missing object and the sound turned out to be part of the same puzzle.",
        ),
        (
            f"Why did {child.id} stop and take a breath?",
            f"{child.id} heard the odd noise and felt worried, so {child.pronoun()} filled each lung slowly and listened instead of rushing. That calm moment helped {child.pronoun('object')} notice the clue.",
        ),
        (
            "How did the flashback help solve the mystery?",
            f"The flashback reminded {child.id} of the earlier uppie moment and where the lucky piece could have gone. That old memory matched the new clue, so the hiding place finally made sense.",
        ),
        (
            f"How did they find {keepsake.label}?",
            f"They used {aid.label} after noticing the clue near {hideout.label}. The tool fit the hiding place, so they could reach or pull the keepsake out instead of only guessing.",
        ),
        (
            "How did the story end?",
            f"They found the missing keepsake and chose a safer place to keep it until parade time. The ending shows that they learned not to leave small special things loose in a busy garage.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"garage", "lung", "flashback"}
    aid = f["aid_cfg"]
    keep = f["keepsake_cfg"]
    hideout = f["hideout_cfg"]
    if aid.id == "magnet_wand":
        tags.add("magnet")
    if aid.id == "step_stool":
        tags.add("stool")
    if keep.id == "bell":
        tags.add("bell")
    if hideout.id == "wheel_hub":
        tags.add("wheel")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ride="wagon",
        keepsake="bell",
        hideout="wheel_hub",
        aid="magnet_wand",
        child_name="Poppy",
        child_gender="girl",
        helper_name="Grandpa Reed",
        helper_type="grandfather",
    ),
    StoryParams(
        ride="scooter",
        keepsake="star",
        hideout="high_shelf_jar",
        aid="step_stool",
        child_name="Theo",
        child_gender="boy",
        helper_name="Aunt May",
        helper_type="aunt",
    ),
    StoryParams(
        ride="soapbox",
        keepsake="whistle",
        hideout="floor_crack",
        aid="magnet_wand",
        child_name="Mira",
        child_gender="girl",
        helper_name="Grandma June",
        helper_type="grandmother",
    ),
]


def explain_rejection(hideout: Hideout, aid: Aid, keepsake: Keepsake) -> str:
    if hideout.kind == "shelf" and not aid.reach_high:
        return (
            f"(No story: {hideout.phrase} is high above the workbench, but {aid.label} cannot reach it. "
            f"Pick a reaching aid like step_stool.)"
        )
    if hideout.kind in {"wheel", "crack"} and not aid.pull_metal:
        return (
            f"(No story: {keepsake.label} is metal and tucked in {hideout.phrase}, but {aid.label} can only help look, not pull it free. "
            f"Pick a magnetic aid.)"
        )
    return "(No story: this aid cannot honestly solve that garage mystery.)"


ASP_RULES = r"""
valid(R, K, H, A) :- ride(R), keepsake(K), hideout(H), aid(A), fits(H, A).

fits(H, A) :- hideout_kind(H, shelf), aid_reach_high(A).
fits(H, A) :- hideout_kind(H, wheel), aid_pull_metal(A).
fits(H, A) :- hideout_kind(H, crack), aid_pull_metal(A).

noise_kind(H, wheel) :- hideout_kind(H, wheel).
noise_kind(H, shelf) :- hideout_kind(H, shelf).
noise_kind(H, crack) :- hideout_kind(H, crack).

#show valid/4.
#show noise_kind/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in RIDES:
        lines.append(asp.fact("ride", rid))
    for kid in KEEPSAKES:
        lines.append(asp.fact("keepsake", kid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("hideout_kind", hid, hideout.kind))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.reach_high:
            lines.append(asp.fact("aid_reach_high", aid_id))
        if aid.pull_metal:
            lines.append(asp.fact("aid_pull_metal", aid_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_noise_kind() -> dict[str, str]:
    import asp

    model = asp.one_model(asp_program())
    return {h: k for (h, k) in asp.atoms(model, "noise_kind")}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale garage mystery storyworld. Unspecified choices are selected at random from valid combinations."
    )
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hideout and args.aid and args.keepsake:
        hideout = HIDEOUTS[args.hideout]
        aid = AIDS[args.aid]
        keepsake = KEEPSAKES[args.keepsake]
        if not aid_fits(hideout, aid, keepsake):
            raise StoryError(explain_rejection(hideout, aid, keepsake))
    elif args.hideout and args.aid:
        hideout = HIDEOUTS[args.hideout]
        aid = AIDS[args.aid]
        sample_keep = next(iter(KEEPSAKES.values()))
        if not aid_fits(hideout, aid, sample_keep):
            raise StoryError(explain_rejection(hideout, aid, sample_keep))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ride is None or combo[0] == args.ride)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ride_id, keepsake_id, hideout_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(sorted(HELPERS))
    helper_name = rng.choice(HELPERS[helper_type])

    return StoryParams(
        ride=ride_id,
        keepsake=keepsake_id,
        hideout=hideout_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ride not in RIDES:
        raise StoryError(f"(Unknown ride: {params.ride})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    ride = RIDES[params.ride]
    keepsake = KEEPSAKES[params.keepsake]
    hideout = HIDEOUTS[params.hideout]
    aid = AIDS[params.aid]
    if not aid_fits(hideout, aid, keepsake):
        raise StoryError(explain_rejection(hideout, aid, keepsake))

    world = tell(
        ride=ride,
        keepsake=keepsake,
        hideout=hideout,
        aid=aid,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    noise_map = asp_noise_kind()
    for hid, hideout in HIDEOUTS.items():
        expect = hideout.kind
        got = noise_map.get(hid)
        if got != expect:
            rc = 1
            print(f"MISMATCH in noise kind for {hid}: asp={got!r} python={expect!r}")
    if rc == 0:
        print("OK: ASP noise classification matches hideout kinds.")

    try:
        smoke_params = CURATED[0]
        smoke = generate(smoke_params)
        if not smoke.story or "garage" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: story text looked wrong.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        sample_params = resolve_params(args, random.Random(17))
        sample = generate(sample_params)
        if not sample.story:
            raise StoryError("(Resolved sample was empty.)")
        print("OK: default resolve/generate path succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ride, keepsake, hideout, aid) combos:\n")
        for ride_id, keepsake_id, hideout_id, aid_id in combos:
            print(f"  {ride_id:8} {keepsake_id:8} {hideout_id:15} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.keepsake} in {p.hideout} ({p.ride}, {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
