#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py
====================================================================================

A standalone story world for a child-facing adventure tale built around a small
rail cart, a segmented track, and a foreshadowed malfunction.

The world model keeps the story grounded:
- the cart rides on a segmented track,
- an early clue foreshadows a later malfunction,
- the guide either heeds the clue and carries the right repair kit, or ignores it
  and must lead everyone on a slower safe recovery,
- the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py --response ignore
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py --malfunction jammed_switch --kit wrench
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/segmentation_track_malfunction_foreshadowing_adventure.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guide_f"}
        male = {"boy", "father", "man", "guide_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"mother", "father"}:
            return {"mother": "mom", "father": "dad"}[self.type]
        if self.role == "guide":
            return "guide"
        return self.label or self.type


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
class Adventure:
    id: str
    place: str
    vehicle: str
    mission: str
    opening_image: str
    ending_image: str
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
class Track:
    id: str
    label: str
    segmentation_line: str
    risky_spot: str
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
class Malfunction:
    id: str
    warning: str
    symptom: str
    cause: str
    need: str
    beat: str
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
class Kit:
    id: str
    label: str
    repairs: set[str] = field(default_factory=set)
    action: str = ""
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


ADVENTURES = {
    "crystal_run": Adventure(
        id="crystal_run",
        place="the Crystal Ridge trail",
        vehicle="a little rail cart",
        mission="find the blue flag at the far lookout",
        opening_image="Bright pennants snapped over the loading platform, and the morning wind smelled like stone and pine.",
        ending_image="At the far lookout, the blue flag flicked in the wind while the cart rested quietly on shining rails.",
        tags={"adventure", "track"},
    ),
    "jungle_span": Adventure(
        id="jungle_span",
        place="the Jungle Span trail",
        vehicle="a handcar",
        mission="cross to the hanging bell on the far platform",
        opening_image="Green vines hung over the station roof, and the wooden platform looked like the start of a secret expedition.",
        ending_image="At the far platform, the hanging bell chimed softly while the handcar waited under the leaves.",
        tags={"adventure", "track"},
    ),
    "moon_pass": Adventure(
        id="moon_pass",
        place="the Moon Pass trail",
        vehicle="a tiny explorer cart",
        mission="reach the silver marker by the ridge window",
        opening_image="The high station felt almost like a moon base, with cool gray rock all around and sky glowing behind it.",
        ending_image="By the ridge window, the silver marker gleamed, and the little cart stood ready for the next brave rider.",
        tags={"adventure", "track"},
    ),
}

TRACKS = {
    "cave_curve": Track(
        id="cave_curve",
        label="cave curve",
        segmentation_line="Blue paint bands split the track into short sections for segmentation, so the guide could watch each part one by one.",
        risky_spot="a bend where the wall came close and the light turned dim",
        supports={"loose_bolt", "dim_sensor", "jammed_switch"},
        tags={"track", "segmentation", "cave"},
    ),
    "bridge_span": Track(
        id="bridge_span",
        label="bridge span",
        segmentation_line="Red stripes marked the track in careful segments across the bridge, like a ladder laid over the air.",
        risky_spot="the middle span above the creek",
        supports={"loose_bolt", "jammed_switch"},
        tags={"track", "segmentation", "bridge"},
    ),
    "ridge_tunnel": Track(
        id="ridge_tunnel",
        label="ridge tunnel",
        segmentation_line="White number marks broke the track into neat segments leading into the tunnel mouth.",
        risky_spot="the tunnel entrance where the wind whistled through the stone",
        supports={"loose_bolt", "dim_sensor"},
        tags={"track", "segmentation", "tunnel"},
    ),
}

MALFUNCTIONS = {
    "loose_bolt": Malfunction(
        id="loose_bolt",
        warning="a tiny tick-tick under the cart seat",
        symptom="the left wheel gave a nervous rattle",
        cause="a loose bolt had worked itself free",
        need="wrench",
        beat="The cart jerked once, then stopped with a hard little shiver.",
        tags={"malfunction", "repair"},
    ),
    "dim_sensor": Malfunction(
        id="dim_sensor",
        warning="the front sensor lamp blinking weaker than it should",
        symptom="the sensor light faded and the cart refused to roll ahead",
        cause="the sensor battery had drained low",
        need="battery",
        beat="The light at the nose of the cart fluttered, blinked twice, and went dark.",
        tags={"malfunction", "repair", "light"},
    ),
    "jammed_switch": Malfunction(
        id="jammed_switch",
        warning="the switch handle giving a stiff little shudder",
        symptom="the switch tongue stuck halfway across the rail",
        cause="the switching pin had jammed in place",
        need="pin",
        beat="Ahead of them, the rail switch gave a sharp clack and froze crooked.",
        tags={"malfunction", "repair", "switch"},
    ),
}

KITS = {
    "wrench": Kit(
        id="wrench",
        label="a small wrench",
        repairs={"loose_bolt"},
        action="tightened the loose bolt with a small wrench until the wheel sat firm again",
        tags={"tool", "repair"},
    ),
    "battery": Kit(
        id="battery",
        label="a spare battery",
        repairs={"dim_sensor"},
        action="snapped in a spare battery and waited for the sensor lamp to glow bright again",
        tags={"tool", "repair", "light"},
    ),
    "pin": Kit(
        id="pin",
        label="a steel guide pin",
        repairs={"jammed_switch"},
        action="slid in a steel guide pin and eased the stubborn switch back into line",
        tags={"tool", "repair", "switch"},
    ),
}

RESPONSES = {
    "heed": "heed",
    "ignore": "ignore",
}

GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Max", "Leo", "Eli", "Theo", "Ben", "Jude"]
GUIDE_NAMES = ["Rosa", "Milo", "Tara", "Jules", "Pia", "Arlo"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    adventure: str
    track: str
    malfunction: str
    kit: str
    response: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    guide_name: str
    guide_gender: str
    segment: int = 3
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules
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
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_warning(world: World) -> list[str]:
    guide = world.get("guide")
    cart = world.get("cart")
    if cart.meters["warning"] < THRESHOLD:
        return []
    sig = ("warning",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide.memes["caution"] += 1
    for kid in world.kids():
        kid.memes["unease"] += 1
    return []


def _r_stuck(world: World) -> list[str]:
    cart = world.get("cart")
    if cart.meters["malfunction"] < THRESHOLD:
        return []
    sig = ("stuck",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cart.meters["stuck"] += 1
    world.get("track").meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("guide").memes["focus"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    cart = world.get("cart")
    if cart.meters["safe_again"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("track").meters["risk"] = 0.0
    for person in [world.get("guide")] + world.kids():
        person.memes["relief"] += 1
        person.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="warning", tag="foreshadow", apply=_r_warning),
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def malfunction_on_track(track: Track, malfunction: Malfunction) -> bool:
    return malfunction.id in track.supports


def kit_fixes(kit: Kit, malfunction: Malfunction) -> bool:
    return malfunction.id in kit.repairs


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for adv_id in ADVENTURES:
        for tr_id, track in TRACKS.items():
            for mal_id, mal in MALFUNCTIONS.items():
                if not malfunction_on_track(track, mal):
                    continue
                for kit_id, kit in KITS.items():
                    if kit_fixes(kit, mal):
                        combos.append((adv_id, tr_id, mal_id, kit_id))
    return combos


def explain_track_mismatch(track: Track, malfunction: Malfunction) -> str:
    return (
        f"(No story: {malfunction.id.replace('_', ' ')} is not a plausible problem on the "
        f"{track.label}. Pick a malfunction that fits that stretch of track.)"
    )


def explain_kit_mismatch(kit: Kit, malfunction: Malfunction) -> str:
    return (
        f"(No story: {kit.label} would not fix {malfunction.id.replace('_', ' ')}. "
        f"The right repair kit for this malfunction is {malfunction.need}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "repaired" if params.response == "heed" else "walked_out"


def predict_if_heeded(track: Track, malfunction: Malfunction, kit: Kit, response: str) -> dict:
    return {
        "warning_matters": response == "heed",
        "repair_ready": kit_fixes(kit, malfunction) and response == "heed",
        "delay": 0 if response == "heed" else 1,
        "safe_exit": True,
        "track_name": track.label,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, guide: Entity, adventure: Adventure) -> None:
    for kid in (hero, friend):
        kid.memes["wonder"] += 1
    world.say(
        f"{adventure.opening_image} {hero.id} and {friend.id} climbed into {adventure.vehicle} with "
        f"{guide.id}, their guide for the morning adventure."
    )
    world.say(
        f'Today they would travel along {adventure.place} and try to {adventure.mission}.'
    )


def show_track(world: World, track: Track) -> None:
    world.say(
        f"The first stretch was the {track.label}. {track.segmentation_line}"
    )


def foreshadow(world: World, hero: Entity, friend: Entity, guide: Entity, track: Track,
               malfunction: Malfunction, kit: Kit, response: str) -> None:
    cart = world.get("cart")
    cart.meters["warning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As they rolled away from the platform, {guide.id} heard {malfunction.warning} and glanced ahead at "
        f"{track.risky_spot}."
    )
    world.say(
        f'"Listen to that," {guide.pronoun()} said softly. "Sometimes a small clue comes before a big problem."'
    )
    if response == "heed":
        world.get("kit").meters["ready"] += 1
        guide.memes["prepared"] += 1
        world.say(
            f"{guide.id} reached into the side box and tucked {kit.label} beside the seat. "
            f'"If this turns into a malfunction, we will be ready," {guide.pronoun()} said.'
        )
    else:
        guide.memes["haste"] += 1
        world.say(
            f"But the line at the station was growing, and {guide.id} decided to keep going without taking "
            f"{kit.label} from the supply shelf."
        )


def ride_deeper(world: World, hero: Entity, friend: Entity, adventure: Adventure, segment: int) -> None:
    hero.memes["bravery"] += 1
    friend.memes["bravery"] += 1
    world.say(
        f"The cart clicked over the first two sections of track, and the adventure felt bigger with every turn. "
        f"By segment {segment}, even the air seemed to hold its breath."
    )


def break_down(world: World, hero: Entity, friend: Entity, malfunction: Malfunction, track: Track) -> None:
    cart = world.get("cart")
    cart.meters["malfunction"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At {track.risky_spot}, {malfunction.beat} {malfunction.symptom.capitalize()}, because {malfunction.cause}."
    )
    world.say(
        f"{hero.id} grabbed the rail, and {friend.id} went still. The adventure no longer felt pretend."
    )


def repair_on_track(world: World, hero: Entity, friend: Entity, guide: Entity,
                    kit: Kit, malfunction: Malfunction) -> None:
    cart = world.get("cart")
    cart.meters["malfunction"] = 0.0
    cart.meters["stuck"] = 0.0
    cart.meters["safe_again"] += 1
    cart.meters["rolling"] += 1
    world.get("kit").meters["used"] += 1
    hero.memes["helpfulness"] += 1
    friend.memes["helpfulness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} did not panic. {guide.pronoun().capitalize()} used {kit.label} and {kit.action}."
    )
    world.say(
        f"{hero.id} held the lamp steady while {friend.id} watched the segment marks on the track. "
        f"In a moment, the little cart gave a calm hum instead of a frightened shake."
    )
    world.say(
        f'"That is why we listen to the first clue," {guide.id} said. Then the cart rolled on again.'
    )


def walk_out(world: World, hero: Entity, friend: Entity, guide: Entity, track: Track,
             malfunction: Malfunction) -> None:
    cart = world.get("cart")
    cart.meters["stuck"] = 1.0
    cart.meters["safe_again"] += 1
    world.get("track").meters["path_open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} pressed the bell cord and called the next station. Without the right kit, "
        f"{guide.pronoun()} could not fix the malfunction there on the track."
    )
    world.say(
        f"So {guide.pronoun()} led the children along the narrow safety path beside the rail, one slow section at a time, "
        f"until they reached the next platform."
    )
    world.say(
        f"The walk was safe, but it was longer and quieter than the ride would have been. "
        f"{hero.id} kept thinking about that first strange sound."
    )


def finish_repaired(world: World, hero: Entity, friend: Entity, guide: Entity, adventure: Adventure) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"{adventure.ending_image} {hero.id} and {friend.id} touched their goal and laughed in the clean wind."
    )
    world.say(
        f"Now the segmented track looked different to them. It was not just part of the game; it was something to watch, respect, and understand."
    )


def finish_walked_out(world: World, hero: Entity, friend: Entity, guide: Entity, adventure: Adventure) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    guide.memes["lesson"] += 1
    world.say(
        f"From the next platform they could still see the far end of {adventure.place}, and the wind made the flags dance as if the trail were calling them back another day."
    )
    world.say(
        f"{guide.id} promised that next time they would check every early clue before setting out. "
        f"{hero.id} nodded, because foreshadowing had turned out to be real life wearing an adventure coat."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(adventure: Adventure, track: Track, malfunction: Malfunction, kit: Kit, response: str,
         child_name: str, child_gender: str, friend_name: str, friend_gender: str,
         guide_name: str, guide_gender: str, segment: int) -> World:
    world = World()
    hero = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    guide_type = "guide_f" if guide_gender == "girl" else "guide_m"
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide"))
    cart = world.add(Entity(id="cart", type="cart", label=adventure.vehicle))
    track_ent = world.add(Entity(id="track", type="track", label=track.label))
    kit_ent = world.add(Entity(id="kit", type="kit", label=kit.label))

    world.facts.update(
        adventure=adventure,
        track_cfg=track,
        malfunction=malfunction,
        kit_cfg=kit,
        response=response,
        segment=segment,
        hero=hero,
        friend=friend,
        guide=guide,
        foreshadowed=True,
        used_kit=False,
        outcome="",
        warning_text=malfunction.warning,
        symptom_text=malfunction.symptom,
    )

    cart.meters["rolling"] = 1.0
    cart.meters["warning"] = 0.0
    cart.meters["malfunction"] = 0.0
    cart.meters["stuck"] = 0.0
    cart.meters["safe_again"] = 0.0
    track_ent.meters["risk"] = 0.0
    kit_ent.meters["ready"] = 0.0
    kit_ent.meters["used"] = 0.0

    introduce(world, hero, friend, guide, adventure)
    show_track(world, track)

    world.para()
    foreshadow(world, hero, friend, guide, track, malfunction, kit, response)
    ride_deeper(world, hero, friend, adventure, segment)

    world.para()
    break_down(world, hero, friend, malfunction, track)

    world.para()
    if response == "heed":
        repair_on_track(world, hero, friend, guide, kit, malfunction)
        world.para()
        finish_repaired(world, hero, friend, guide, adventure)
        world.facts["used_kit"] = True
        world.facts["outcome"] = "repaired"
    else:
        walk_out(world, hero, friend, guide, track, malfunction)
        world.para()
        finish_walked_out(world, hero, friend, guide, adventure)
        world.facts["used_kit"] = False
        world.facts["outcome"] = "walked_out"

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "segmentation": [
        (
            "What does segmentation mean on a track?",
            "Segmentation means the track is split into smaller sections that are easy to watch and check. Those sections help people notice where a problem starts."
        )
    ],
    "track": [
        (
            "What is a track?",
            "A track is the path that a cart or train follows. It guides the wheels so the ride goes the right way."
        )
    ],
    "malfunction": [
        (
            "What is a malfunction?",
            "A malfunction is when a machine does not work the way it should. It can be a small problem, but it still needs attention."
        )
    ],
    "repair": [
        (
            "Why do guides carry repair tools?",
            "Guides carry repair tools so they can fix small problems safely and quickly. The right tool can stop a little trouble from becoming a bigger delay."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is an early clue that hints something important will happen later. It helps the middle of the story feel earned instead of sudden."
        )
    ],
}

KNOWLEDGE_ORDER = ["segmentation", "track", "malfunction", "repair", "foreshadowing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    adv = f["adventure"]
    mal = f["malfunction"]
    track = f["track_cfg"]
    hero = f["hero"]
    guide = f["guide"]
    response = f["response"]
    base = (
        'Write a short adventure story for a 3-to-5-year-old that uses the words '
        '"segmentation", "track", and "malfunction".'
    )
    if response == "heed":
        return [
            base,
            f"Tell a gentle adventure where {guide.id}, a guide, notices an early clue on a segmented {track.label} and that clue helps {guide.pronoun('object')} fix a later malfunction.",
            f"Write a story where {hero.id} rides toward {adv.mission}, hears a warning first, and learns that careful watching can keep an adventure moving."
        ]
    return [
        base,
        f"Tell an adventure where {guide.id} hears an early clue on the {track.label} but keeps going, and later a malfunction forces everyone to leave the cart and walk safely to the next station.",
        f"Write a foreshadowing story where a strange sound on the track matters later, and the children learn to respect early warning signs."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guide = f["guide"]
    adv = f["adventure"]
    track = f["track_cfg"]
    mal = f["malfunction"]
    kit = f["kit_cfg"]
    segment = f["segment"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children riding with their guide {guide.id}. They are trying to {adv.mission} along {adv.place}."
        ),
        (
            "What made the story feel like an adventure at the beginning?",
            f"The children climbed into {adv.vehicle} and set out along a high, exciting trail. The flags, wind, and faraway goal made the ride feel bold and important."
        ),
        (
            "What clue came before the problem?",
            f"The first clue was {mal.warning}. That was foreshadowing, because it hinted that something on the track might soon go wrong."
        ),
        (
            "What happened at segment "
            f"{segment}?",
            f"At segment {segment}, the cart had a malfunction on the {track.label}. {mal.beat} {mal.symptom.capitalize()}, so the ride could not go on the same way."
        ),
    ]
    if response == "heed":
        qa.append(
            (
                f"How did {guide.id} solve the problem?",
                f"{guide.id} had listened to the early clue and carried {kit.label}. Because the right repair kit was ready, {guide.pronoun()} could fix the malfunction there on the track and let the cart roll again."
            )
        )
        qa.append(
            (
                "Why did the early clue matter?",
                f"It mattered because it changed what {guide.id} did before the cart reached trouble. The warning led {guide.pronoun('object')} to bring {kit.label}, and that is what saved the ride from turning into a long delay."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children reaching their goal and seeing the trail in a new way. They still felt adventurous, but now they also understood that a segmented track should be watched with care."
            )
        )
    else:
        qa.append(
            (
                f"Why did they have to walk to the next station?",
                f"They had to walk because the cart's malfunction happened far from the platform and {guide.id} did not have the repair kit on board. The safety path let them get out carefully, but it took longer because the first clue had been ignored."
            )
        )
        qa.append(
            (
                "What did the children learn at the end?",
                f"They learned that little clues can matter even when an adventure feels exciting. The strange sound on the track seemed small at first, but later it explained why the ride had to stop."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely on the next platform instead of at the far goal. The flags were still dancing in the wind, but now the children were thinking about warning signs as much as adventure."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"segmentation", "track", "malfunction", "foreshadowing", "repair"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        adventure="crystal_run",
        track="cave_curve",
        malfunction="loose_bolt",
        kit="wrench",
        response="heed",
        child_name="Lina",
        child_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        guide_name="Rosa",
        guide_gender="girl",
        segment=3,
    ),
    StoryParams(
        adventure="jungle_span",
        track="bridge_span",
        malfunction="jammed_switch",
        kit="pin",
        response="heed",
        child_name="Max",
        child_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        guide_name="Arlo",
        guide_gender="boy",
        segment=4,
    ),
    StoryParams(
        adventure="moon_pass",
        track="ridge_tunnel",
        malfunction="dim_sensor",
        kit="battery",
        response="ignore",
        child_name="Ava",
        child_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        guide_name="Jules",
        guide_gender="boy",
        segment=3,
    ),
    StoryParams(
        adventure="crystal_run",
        track="cave_curve",
        malfunction="jammed_switch",
        kit="pin",
        response="ignore",
        child_name="Nora",
        child_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        guide_name="Tara",
        guide_gender="girl",
        segment=4,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(A,T,M,K) :- adventure(A), track(T), malfunction(M), kit(K),
                  supports(T,M), repairs(K,M).

outcome(repaired) :- response(heed).
outcome(walked_out) :- response(ignore).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for tid, track in TRACKS.items():
        lines.append(asp.fact("track", tid))
        for mid in sorted(track.supports):
            lines.append(asp.fact("supports", tid, mid))
    for mid in MALFUNCTIONS:
        lines.append(asp.fact("malfunction", mid))
    for kid, kit in KITS.items():
        lines.append(asp.fact("kit", kid))
        for mid in sorted(kit.repairs):
            lines.append(asp.fact("repairs", kid, mid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(response: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("response", response)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    bad = 0
    for response in RESPONSES:
        if asp_outcome(response) != ("repaired" if response == "heed" else "walked_out"):
            bad += 1
    if bad == 0:
        print("OK: outcome model matches Python response logic.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome cases differ.")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        parser = build_parser()
        resolved = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(resolved)
        if not sample.story.strip():
            raise StoryError("default resolved generation was empty")
        print("OK: default generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {exc}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world: a segmented track, an early clue, and a later malfunction."
    )
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--track", choices=TRACKS)
    ap.add_argument("--malfunction", choices=MALFUNCTIONS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--segment", type=int, choices=[2, 3, 4], help="which numbered segment the cart reaches before the trouble")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible adventure/track/malfunction/kit combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.track and args.malfunction:
        track = TRACKS[args.track]
        malfunction = MALFUNCTIONS[args.malfunction]
        if not malfunction_on_track(track, malfunction):
            raise StoryError(explain_track_mismatch(track, malfunction))
    if args.kit and args.malfunction:
        kit = KITS[args.kit]
        malfunction = MALFUNCTIONS[args.malfunction]
        if not kit_fixes(kit, malfunction):
            raise StoryError(explain_kit_mismatch(kit, malfunction))

    combos = [
        combo for combo in valid_combos()
        if (args.adventure is None or combo[0] == args.adventure)
        and (args.track is None or combo[1] == args.track)
        and (args.malfunction is None or combo[2] == args.malfunction)
        and (args.kit is None or combo[3] == args.kit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    adventure, track, malfunction, kit = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    segment = args.segment if args.segment is not None else rng.choice([2, 3, 4])

    child_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=child_name)
    guide_gender = rng.choice(["girl", "boy"])
    guide_name = rng.choice(GUIDE_NAMES)

    return StoryParams(
        adventure=adventure,
        track=track,
        malfunction=malfunction,
        kit=kit,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
        segment=segment,
    )


def generate(params: StoryParams) -> StorySample:
    if params.adventure not in ADVENTURES:
        raise StoryError(f"(Unknown adventure: {params.adventure})")
    if params.track not in TRACKS:
        raise StoryError(f"(Unknown track: {params.track})")
    if params.malfunction not in MALFUNCTIONS:
        raise StoryError(f"(Unknown malfunction: {params.malfunction})")
    if params.kit not in KITS:
        raise StoryError(f"(Unknown kit: {params.kit})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    adventure = ADVENTURES[params.adventure]
    track = TRACKS[params.track]
    malfunction = MALFUNCTIONS[params.malfunction]
    kit = KITS[params.kit]

    if not malfunction_on_track(track, malfunction):
        raise StoryError(explain_track_mismatch(track, malfunction))
    if not kit_fixes(kit, malfunction):
        raise StoryError(explain_kit_mismatch(kit, malfunction))

    world = tell(
        adventure=adventure,
        track=track,
        malfunction=malfunction,
        kit=kit,
        response=params.response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        segment=params.segment,
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
        print(f"{len(combos)} compatible (adventure, track, malfunction, kit) combos:\n")
        for adventure, track, malfunction, kit in combos:
            print(f"  {adventure:12} {track:12} {malfunction:13} {kit}")
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
            header = (
                f"### {p.child_name} & {p.friend_name}: {p.malfunction} on {p.track} "
                f"({p.adventure}, {p.response})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
