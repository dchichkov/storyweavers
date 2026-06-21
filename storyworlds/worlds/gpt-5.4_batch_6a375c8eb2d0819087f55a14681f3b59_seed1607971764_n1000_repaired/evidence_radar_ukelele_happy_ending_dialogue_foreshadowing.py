#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py
=========================================================================================

A standalone story world for a tiny Space-Adventure tale:

A child on a family spaceship loses a beloved ukelele, spots a strange reading on
the radar, gathers evidence instead of guessing, and discovers the harmless cause.
The clues are foreshadowed early, the middle is driven by simulated state, and the
ending proves what changed: fear gives way to relief, and the ukelele comes home.

Run it
------
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py --setting greenhouse_ring --cause air_draft
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py --radar heat
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py --all
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/evidence_radar_ukelele_happy_ending_dialogue_foreshadowing.py --verify
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
    label: str
    window_view: str
    hideout: str
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
class Cause:
    id: str
    mover: str
    simple_name: str
    foreshadow: str
    clue1: str
    clue2: str
    radar_signature: str
    found_place: str
    detect_modes: set[str] = field(default_factory=set)
    response: str = ""
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
class RadarMode:
    id: str
    label: str
    verb: str
    reading: str
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
    text: str
    qa_text: str
    works_for: set[str] = field(default_factory=set)
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
        self.facts: dict = {
            "mystery_active": False,
            "radar_ping": False,
            "detectable": False,
            "evidence_count": 0,
            "response_applied": False,
            "source_identified": False,
            "found": False,
        }

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


def _r_mystery_worry(world: World) -> list[str]:
    if not world.facts["mystery_active"]:
        return []
    sig = ("mystery_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["fear"] += 1
    helper.memes["curiosity"] += 1
    return []


def _r_radar_hope(world: World) -> list[str]:
    if not (world.facts["radar_ping"] and world.facts["detectable"]):
        return []
    sig = ("radar_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["hope"] += 1
    helper.memes["confidence"] += 1
    return []


def _r_identify(world: World) -> list[str]:
    if not (world.facts["radar_ping"] and world.facts["detectable"]):
        return []
    if world.facts["evidence_count"] < 2:
        return []
    sig = ("identify",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["source_identified"] = True
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["fear"] = 0.0
    hero.memes["curiosity"] += 1
    helper.memes["confidence"] += 1
    return []


def _r_resolution(world: World) -> list[str]:
    if not (world.facts["source_identified"] and world.facts["response_applied"]):
        return []
    sig = ("resolution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["found"] = True
    hero = world.get("hero")
    helper = world.get("helper")
    uke = world.get("ukelele")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    uke.meters["returned"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery_worry", tag="emotion", apply=_r_mystery_worry),
    Rule(name="radar_hope", tag="emotion", apply=_r_radar_hope),
    Rule(name="identify", tag="knowledge", apply=_r_identify),
    Rule(name="resolution", tag="physical", apply=_r_resolution),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "docking_hall": Setting(
        id="docking_hall",
        label="the docking hall",
        window_view="freighters blinking against a field of stars",
        hideout="beside the charging rail under the silver catwalk",
        affords={"service_robot"},
        tags={"ship", "robot"},
    ),
    "greenhouse_ring": Setting(
        id="greenhouse_ring",
        label="the greenhouse ring",
        window_view="tiny moons hanging over rows of floating tomatoes",
        hideout="looped around a vine ladder near the air vent",
        affords={"air_draft"},
        tags={"ship", "air"},
    ),
    "observatory_deck": Setting(
        id="observatory_deck",
        label="the observatory deck",
        window_view="a purple nebula spread like paint across the dark",
        hideout="curled under the star map bench",
        affords={"moon_pup"},
        tags={"ship", "pet"},
    ),
}

CAUSES = {
    "service_robot": Cause(
        id="service_robot",
        mover="the little service robot",
        simple_name="a helpful robot",
        foreshadow="From far down the hall came a polite beep-beep, as if something small had answered the final chord.",
        clue1="On the floor they found two neat wheel lines in the dust.",
        clue2='Near the wall, a tiny robot voice said, "Object tidied. Object tidied."',
        radar_signature="a slow-stop blinking dot",
        found_place="beside the charging rail under the silver catwalk",
        detect_modes={"motion", "metal"},
        response="call_robot",
        tags={"robot", "evidence"},
    ),
    "air_draft": Cause(
        id="air_draft",
        mover="a playful air draft",
        simple_name="a strong puff of air",
        foreshadow="A soft twang drifted back from the vent grate, and one loose leaf fluttered in the hallway light.",
        clue1="A ribbon from the ukelele strap was fluttering toward the vent.",
        clue2="The vent grill was open a finger-width, and cool air whistled through it.",
        radar_signature="a wobbly silver echo",
        found_place="looped around a vine ladder near the air vent",
        detect_modes={"motion", "metal"},
        response="close_vent",
        tags={"air", "evidence"},
    ),
    "moon_pup": Cause(
        id="moon_pup",
        mover="the moon pup",
        simple_name="their playful moon pup",
        foreshadow="Somewhere above the sleeping pods came a happy little yip, and then the sound of tiny feet skittering away.",
        clue1="Shiny paw prints curved across the deck in a zigzag line.",
        clue2="A silver chew mark showed on the ukelele strap hook.",
        radar_signature="a quick zigzag glow",
        found_place="curled under the star map bench",
        detect_modes={"motion", "heat"},
        response="whistle_pup",
        tags={"pet", "evidence"},
    ),
}

RADAR_MODES = {
    "motion": RadarMode(
        id="motion",
        label="motion radar",
        verb="swept the motion radar in a careful arc",
        reading="looking for something that was still moving",
        tags={"radar"},
    ),
    "metal": RadarMode(
        id="metal",
        label="metal radar",
        verb="clicked the metal radar on and turned the bright ring slowly",
        reading="looking for a small metal shape, like tuning pegs and strings",
        tags={"radar"},
    ),
    "heat": RadarMode(
        id="heat",
        label="heat radar",
        verb="raised the heat radar and watched its warm little screen",
        reading="looking for a warm battery or body tucked somewhere cozy",
        tags={"radar"},
    ),
}

RESPONSES = {
    "call_robot": Response(
        id="call_robot",
        text='knelt by the charging rail and said, "Helper Bot, please bring that instrument here." The little robot rolled out at once with the ukelele balanced carefully on its tray',
        qa_text="called the little robot back and had it carry the ukelele over",
        works_for={"service_robot"},
        tags={"robot"},
    ),
    "close_vent": Response(
        id="close_vent",
        text='shut the vent, reached up the vine ladder, and gently lifted the ukelele free before the next gust could tug it away again',
        qa_text="closed the vent and lifted the ukelele down safely",
        works_for={"air_draft"},
        tags={"air"},
    ),
    "whistle_pup": Response(
        id="whistle_pup",
        text='gave the moon pup its three-note dinner whistle, and the little creature scampered out, proudly dragging the ukelele by its strap',
        qa_text="used the moon pup's dinner whistle and coaxed it out with the ukelele",
        works_for={"moon_pup"},
        tags={"pet"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nia", "Tara", "Ivy", "Zoe", "Ada", "Nova"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Owen", "Kai", "Eli", "Theo", "Arin"]
TRAITS = ["brave", "curious", "gentle", "careful", "cheerful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid in sorted(setting.affords):
            cause = CAUSES[cid]
            for rid in sorted(cause.detect_modes):
                for resp_id, resp in RESPONSES.items():
                    if cid in resp.works_for:
                        combos.append((sid, cid, rid, resp_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    cause: str
    radar: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
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


def cause_allowed(setting_id: str, cause_id: str) -> bool:
    return cause_id in SETTINGS[setting_id].affords


def detects(radar_id: str, cause_id: str) -> bool:
    return radar_id in CAUSES[cause_id].detect_modes


def response_works(response_id: str, cause_id: str) -> bool:
    return cause_id in RESPONSES[response_id].works_for


def explain_setting(setting_id: str, cause_id: str) -> str:
    return (
        f"(No story: {CAUSES[cause_id].mover} is not the kind of thing this world places in "
        f"{SETTINGS[setting_id].label}. Pick a setting that really affords that cause.)"
    )


def explain_radar(radar_id: str, cause_id: str) -> str:
    return (
        f"(No story: {RADAR_MODES[radar_id].label} would not honestly find {CAUSES[cause_id].simple_name}. "
        f"Pick a radar mode that can detect that cause.)"
    )


def explain_response(response_id: str, cause_id: str) -> str:
    return (
        f"(No story: response '{response_id}' does not fit {CAUSES[cause_id].simple_name}. "
        f"The grown-up's fix has to match the real cause.)"
    )


def predict_signal(world: World, cause: Cause, radar: RadarMode) -> dict:
    sim = world.copy()
    sim.facts["radar_ping"] = True
    sim.facts["detectable"] = radar.id in cause.detect_modes
    propagate(sim, narrate=False)
    return {
        "detectable": sim.facts["detectable"],
        "hope": sim.get("hero").memes["hope"],
    }


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity, setting: Setting, cause: Cause) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} lived with {helper.id} and their {parent.label_word} on a small family ship. "
        f"That evening they were in {setting.label}, where the round windows showed {setting.window_view}."
    )
    world.say(
        f"{hero.id} liked to carry a tiny ukelele everywhere and strum soft space songs while the lights blinked blue."
    )
    world.say(cause.foreshadow)
    world.say(
        f'"Did you hear that?" {helper.id} asked. "{hero.id}, that sounded like a clue."'
    )


def lose_ukelele(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    uke = world.get("ukelele")
    uke.meters["missing"] += 1
    world.facts["mystery_active"] = True
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"A little later, {hero.id} turned to hang the ukelele on its hook, but the hook was empty."
    )
    world.say(
        f'"My ukelele is gone," {hero.id} whispered. For one small moment, the quiet ship felt much bigger.'
    )
    world.say(
        f'"Maybe a space thief took it," {hero.pronoun()} said.'
    )
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "Let\'s look for evidence before we decide that."'
    )
    world.say(
        f"{helper.id} pointed toward the dark end of {setting.label}, where the shadows seemed full of questions."
    )


def radar_scan(world: World, hero: Entity, helper: Entity, parent: Entity, radar: RadarMode, cause: Cause) -> None:
    world.para()
    pred = predict_signal(world, cause, radar)
    world.facts["predicted_detectable"] = pred["detectable"]
    world.say(
        f'{parent.label_word.capitalize()} opened a drawer in the wall and handed {helper.id} the {radar.label}. '
        f'"If we want the truth," {parent.pronoun()} said, "we use tools and we use our eyes."'
    )
    world.say(
        f"{helper.id} {radar.verb}, {radar.reading}."
    )
    if radar.id in cause.detect_modes:
        world.facts["radar_ping"] = True
        world.facts["detectable"] = True
        propagate(world, narrate=False)
        world.say(
            f'Soon a mark appeared on the screen: {cause.radar_signature}, leading toward {cause.found_place}.'
        )
        world.say(
            f'"The radar found something," {helper.id} said. "{hero.id}, stay with me."'
        )
    else:
        world.say(
            f"But the screen stayed blank. Without a real reading, they had no honest path to follow."
        )


def collect_evidence(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    world.para()
    world.say(
        f"The two children followed the reading slowly, boots whispering on the floor."
    )
    world.say(cause.clue1)
    world.facts["evidence_count"] += 1
    world.say(cause.clue2)
    world.facts["evidence_count"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"That is evidence," {helper.id} said softly. "Now the mystery feels smaller."'
    )
    if world.facts["source_identified"]:
        world.say(
            f'{hero.id} took a brave breath. "So it was {cause.simple_name}, not a space thief after all."'
        )


def retrieve(world: World, hero: Entity, helper: Entity, parent: Entity, cause: Cause, response: Response) -> None:
    world.para()
    world.facts["response_applied"] = True
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} smiled a calm captain smile and {response.text}.'
    )
    world.say(
        f'The mystery opened up all at once. It was only {cause.simple_name}, and the ukelele was safe.'
    )
    world.say(
        f'"I was scared for nothing," {hero.id} said.'
    )
    world.say(
        f'"Not for nothing," {parent.label_word} said. "You were scared, and then you looked for evidence."'
    )


def ending(world: World, hero: Entity, helper: Entity, parent: Entity, setting: Setting) -> None:
    world.para()
    hero.memes["courage"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{hero.id} hugged the ukelele close, then strummed one bright note that skipped against the windows.'
    )
    world.say(
        f'"Play the happy one," {helper.id} said.'
    )
    world.say(
        f"So {hero.id} played, {helper.id} hummed along, and even {parent.label_word} tapped the rail in time."
    )
    world.say(
        f"Out beyond {setting.label}, the stars kept shining, but now they looked like friendly lanterns instead of secret eyes."
    )


def tell(
    setting: Setting,
    cause: Cause,
    radar: RadarMode,
    response: Response,
    hero_name: str = "Luna",
    hero_gender: str = "girl",
    helper_name: str = "Milo",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, role="helper", label=helper_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the captain"))
    uke = world.add(Entity(id="ukelele", kind="thing", type="instrument", label="ukelele"))

    hero.attrs["name"] = hero_name
    helper.attrs["name"] = helper_name
    parent.attrs["captain"] = True
    hero.traits.append(trait)
    hero.memes["fear"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["curiosity"] = 0.0
    helper.memes["confidence"] = 0.0
    parent.memes["calm"] = 1.0
    uke.meters["missing"] = 0.0
    uke.meters["returned"] = 0.0

    world.facts.update(
        setting=setting,
        cause=cause,
        radar=radar,
        response=response,
        hero=hero,
        helper=helper,
        parent=parent,
        uke=uke,
        hero_name=hero_name,
        helper_name=helper_name,
    )

    introduce(world, hero, helper, parent, setting, cause)
    lose_ukelele(world, hero, helper, setting)
    radar_scan(world, hero, helper, parent, radar, cause)
    collect_evidence(world, hero, helper, cause)
    retrieve(world, hero, helper, parent, cause, response)
    ending(world, hero, helper, parent, setting)

    world.facts["happy_ending"] = world.facts["found"] and uke.meters["returned"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "radar": [
        (
            "What does radar do?",
            "Radar is a tool that helps you notice where something is, even when it is far away or hard to see. It gives you a clue about where to look next.",
        )
    ],
    "evidence": [
        (
            "What is evidence?",
            "Evidence is a clue that helps you know what really happened. Good evidence keeps you from guessing wildly.",
        )
    ],
    "ukelele": [
        (
            "What is a ukelele?",
            "A ukelele is a small string instrument you can hold in your arms and strum with your fingers. It makes bright, cheerful music.",
        )
    ],
    "robot": [
        (
            "What is a service robot?",
            "A service robot is a little helper machine that carries, cleans, or tidies things. It follows jobs, so sometimes it moves objects very carefully.",
        )
    ],
    "air": [
        (
            "Can air move light things?",
            "Yes. A strong puff of air can tug ribbons, paper, or other light objects and push them somewhere else.",
        )
    ],
    "pet": [
        (
            "Why do playful pets carry things away?",
            "Playful pets sometimes grab straps or toys because they think it is a game. They are not being mean; they are inviting play.",
        )
    ],
}
KNOWLEDGE_ORDER = ["evidence", "radar", "ukelele", "robot", "air", "pet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    cause = f["cause"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        'Write a short space adventure for a 3-to-5-year-old that includes the words "evidence", "radar", and "ukelele".',
        f"Tell a gentle mystery on a spaceship where {hero.attrs['name']} loses a ukelele, {helper.attrs['name']} says they should look for evidence, and the answer turns out to be {cause.simple_name}.",
        f"Write a story with dialogue, foreshadowing, and a happy ending in {setting.label}, where a radar clue helps children solve a small mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    cause = f["cause"]
    radar = f["radar"]
    response = f["response"]
    setting = f["setting"]
    hero_name = f["hero_name"]
    helper_name = f["helper_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {helper_name}, two children on a family spaceship, and their {parent.label_word} who helps them at the end.",
        ),
        (
            "What was missing?",
            f"{hero_name}'s ukelele was missing from its hook. That is what turned the quiet evening into a mystery.",
        ),
        (
            f"Why did {helper_name} tell {hero_name} to look for evidence?",
            f"{helper_name} did not want them to guess that a space thief had come. Looking for evidence would show what really happened and make the mystery smaller.",
        ),
        (
            "How did the radar help?",
            f"They used the {radar.label}, and it showed {cause.radar_signature} leading toward {cause.found_place}. The radar gave them a direction, so their clue hunt had a real path.",
        ),
        (
            "What evidence did they find?",
            f"{cause.clue1} {cause.clue2} Those clues matched {cause.simple_name}, so the children could stop imagining something scarier.",
        ),
        (
            "How did they get the ukelele back?",
            f"Their {parent.label_word} {response.qa_text}. That solved the real problem because it fit the cause they had discovered.",
        ),
        (
            "How did the story end?",
            f"It ended happily with the ukelele safe in {hero_name}'s arms and a bright song in {setting.label}. The stars felt friendly again because the mystery had been solved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"evidence", "radar", "ukelele"} | set(world.facts["cause"].tags)
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
    for eid, ent in world.entities.items():
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
        lines.append(f"  {eid:8} ({ent.type:10}) {' '.join(bits)}")
    shown_facts = {
        k: v for k, v in world.facts.items()
        if isinstance(v, (str, int, float, bool))
    }
    lines.append(f"  facts={shown_facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="docking_hall",
        cause="service_robot",
        radar="motion",
        response="call_robot",
        hero="Luna",
        hero_gender="girl",
        helper="Milo",
        helper_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="greenhouse_ring",
        cause="air_draft",
        radar="metal",
        response="close_vent",
        hero="Leo",
        hero_gender="boy",
        helper="Nova",
        helper_gender="girl",
        parent="father",
        trait="careful",
    ),
    StoryParams(
        setting="observatory_deck",
        cause="moon_pup",
        radar="heat",
        response="whistle_pup",
        hero="Mira",
        hero_gender="girl",
        helper="Finn",
        helper_gender="boy",
        parent="mother",
        trait="brave",
    ),
]


ASP_RULES = r"""
valid(S, C, R, P) :- setting(S), cause(C), radar(R), response(P),
                     affords(S, C), detects(R, C), works(P, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for cid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, cid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for rid in sorted(cause.detect_modes):
            lines.append(asp.fact("detects", rid, cid))
    for rid in RADAR_MODES:
        lines.append(asp.fact("radar", rid))
    for pid, resp in RESPONSES.items():
        lines.append(asp.fact("response", pid))
        for cid in sorted(resp.works_for):
            lines.append(asp.fact("works", pid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(12):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE SETUP FAILED at seed {seed}.")
            break

    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: single generate() smoke test produced story text.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    bad = 0
    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                bad += 1
        except Exception:
            bad += 1
    if bad == 0:
        print(f"OK: generated {len(smoke_cases)} smoke-test stories without crashing.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(smoke_cases)} smoke-test stories failed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lost ukelele, a radar clue, and evidence on a family spaceship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--radar", choices=RADAR_MODES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the inline ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause and not cause_allowed(args.setting, args.cause):
        raise StoryError(explain_setting(args.setting, args.cause))
    if args.cause and args.radar and not detects(args.radar, args.cause):
        raise StoryError(explain_radar(args.radar, args.cause))
    if args.cause and args.response and not response_works(args.response, args.cause):
        raise StoryError(explain_response(args.response, args.cause))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
        and (args.radar is None or combo[2] == args.radar)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cause_id, radar_id, response_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        cause=cause_id,
        radar=radar_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.radar not in RADAR_MODES:
        raise StoryError(f"(Unknown radar mode: {params.radar})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not cause_allowed(params.setting, params.cause):
        raise StoryError(explain_setting(params.setting, params.cause))
    if not detects(params.radar, params.cause):
        raise StoryError(explain_radar(params.radar, params.cause))
    if not response_works(params.response, params.cause):
        raise StoryError(explain_response(params.response, params.cause))

    world = tell(
        setting=SETTINGS[params.setting],
        cause=CAUSES[params.cause],
        radar=RADAR_MODES[params.radar],
        response=RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cause, radar, response) combos:\n")
        for setting_id, cause_id, radar_id, response_id in combos:
            print(f"  {setting_id:16} {cause_id:14} {radar_id:8} {response_id}")
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
            header = f"### {p.hero} & {p.helper}: {p.cause} in {p.setting} ({p.radar}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
