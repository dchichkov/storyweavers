#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py
================================================================================================

A standalone storyworld for a small adventure tale where two children explore a
mysterious place, notice a *characteristic* sound that hints at an *exit*, and
use the right tool to get out safely.

The world model is built around three things:

1. A setting that can carry a plausible clue-sound toward an exit.
2. An obstacle that needs a matching piece of gear.
3. A decision beat where the hero either trusts the clue quickly or takes a
   brief wrong turn before learning to listen.

The prose intentionally uses sound effects, foreshadowing, and inner monologue
as part of the simulated state, rather than as detached style tags.

Run it
------
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py --place sea_cave --sound waves --obstacle slippery_ledge --gear grip_boots
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py --place old_mine --sound gulls
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exit_characteristic_sound_effects_foreshadowing_inner_monologue.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


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
    treasure: str
    warning: str
    exit_kind: str
    sound_tags: set[str] = field(default_factory=set)
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
class SoundClue:
    id: str
    label: str
    effect: str
    source: str
    hint: str
    carries_in: set[str] = field(default_factory=set)
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
    scene: str
    need: str
    fix_text: str
    fail_text: str
    danger: str
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
class Gear:
    id: str
    label: str
    phrase: str
    grants: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    sound: str
    obstacle: str
    gear: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    guardian: str
    trait: str
    urgency: int = 1
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


PLACES = {
    "sea_cave": Place(
        id="sea_cave",
        label="sea cave",
        opening="a sea cave with shining walls and old rope marks near the mouth",
        treasure="a tiny brass compass charm tucked on a shelf of rock",
        warning="Far away, the tide gave a slow hush-roar that sounded bigger each time.",
        exit_kind="the crack where daylight touched the rocks",
        sound_tags={"waves", "wind"},
        tags={"cave", "sea"},
    ),
    "old_mine": Place(
        id="old_mine",
        label="old mine",
        opening="an old mine tunnel with wooden beams and silver dust sparkling on the floor",
        treasure="a smooth stone with a star shape hidden in a shallow cart",
        warning="Somewhere ahead, a beam gave a tired creak... creak... as if the tunnel wanted everyone to hurry.",
        exit_kind="the side exit under the square warning sign",
        sound_tags={"wind", "drip"},
        tags={"mine", "underground"},
    ),
    "sun_temple": Place(
        id="sun_temple",
        label="sun temple",
        opening="a sun temple hallway with lion carvings and bright chips of gold paint",
        treasure="a little sun token resting in a cracked bowl",
        warning="Dust drifted from the ceiling with every distant thump, like the place was clearing its throat.",
        exit_kind="the ivy-framed exit behind the carved wall",
        sound_tags={"birds", "wind"},
        tags={"temple", "ruin"},
    ),
}

SOUNDS = {
    "waves": SoundClue(
        id="waves",
        label="waves",
        effect="Hush-roar... hush-roar...",
        source="sea water pushing through a narrow gap",
        hint="The steady sea sound meant open air and shore were nearby.",
        carries_in={"sea_cave"},
        tags={"waves", "sound"},
    ),
    "wind": SoundClue(
        id="wind",
        label="wind",
        effect="Whooo... whooo...",
        source="wind slipping through a crack",
        hint="The moving air and soft whistle pointed toward an opening.",
        carries_in={"sea_cave", "old_mine", "sun_temple"},
        tags={"wind", "sound"},
    ),
    "drip": SoundClue(
        id="drip",
        label="dripping water",
        effect="Plink... plink... plink...",
        source="water falling beside a tunnel that led outside",
        hint="The regular dripping marked the cooler tunnel where fresh air slipped in.",
        carries_in={"old_mine"},
        tags={"drip", "sound"},
    ),
    "birds": SoundClue(
        id="birds",
        label="birds",
        effect="Caw-caw! Chirp-chirp!",
        source="birds nesting near broken stone above an outer wall",
        hint="Bird calls meant sky, branches, and a way out close by.",
        carries_in={"sun_temple"},
        tags={"birds", "sound"},
    ),
}

OBSTACLES = {
    "dark_turn": Obstacle(
        id="dark_turn",
        label="dark turn",
        scene="a bend so dark that the floor vanished into black",
        need="light",
        fix_text="raised the light and showed the safe edges of the path",
        fail_text="could not show where the floor dropped away",
        danger="Without light, one wrong step could send pebbles skittering into the dark.",
        tags={"dark", "careful"},
    ),
    "slippery_ledge": Obstacle(
        id="slippery_ledge",
        label="slippery ledge",
        scene="a narrow ledge shiny with damp moss",
        need="grip",
        fix_text="pressed onto the stone and kept little feet from sliding",
        fail_text="kept slipping on the wet stone",
        danger="A skid there would mean a bump, a scare, and a hard scramble back.",
        tags={"slippery", "careful"},
    ),
    "high_grate": Obstacle(
        id="high_grate",
        label="high grate",
        scene="a small iron grate with its latch just out of reach",
        need="reach",
        fix_text="hooked the latch and tugged the grate wide open",
        fail_text="could not reach the latch at all",
        danger="If they could not reach it, they would lose time while the place grew louder and gloomier.",
        tags={"grate", "careful"},
    ),
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        grants={"light"},
        tags={"light"},
    ),
    "grip_boots": Gear(
        id="grip_boots",
        label="grip boots",
        phrase="a pair of grip boots",
        grants={"grip"},
        tags={"boots"},
    ),
    "hook_pole": Gear(
        id="hook_pole",
        label="hook pole",
        phrase="a fold-up hook pole",
        grants={"reach"},
        tags={"hook"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ivy", "Suri", "Aya", "Zoe"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Rami", "Theo", "Milo", "Kai", "Ben"]
TRAITS = ["careful", "brave", "curious", "thoughtful", "steady", "patient"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("exit_found"):
        return out
    for child_id in ("hero", "friend"):
        ent = world.get(child_id)
        if ent.meters["warning"] >= THRESHOLD:
            sig = ("fear", child_id, int(ent.meters["warning"]))
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["fear"] += 1
            out.append("__warning__")
    return out


def _r_detour(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("took_detour") and not world.facts.get("exit_found"):
        sig = ("detour", 1)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["danger"] += 1
            world.get("hero").memes["doubt"] += 1
            world.get("friend").memes["trust"] += 1
            out.append("__detour__")
    return out


CAUSAL_RULES = [
    Rule(name="warning", tag="emotional", apply=_r_warning),
    Rule(name="detour", tag="physical", apply=_r_detour),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def sound_fits(place: Place, sound: SoundClue) -> bool:
    return place.id in sound.carries_in and sound.id in place.sound_tags


def gear_matches(obstacle: Obstacle, gear: Gear) -> bool:
    return obstacle.need in gear.grants


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for sound_id, sound in SOUNDS.items():
            if not sound_fits(place, sound):
                continue
            for obstacle_id, obstacle in OBSTACLES.items():
                for gear_id, gear in GEAR.items():
                    if gear_matches(obstacle, gear):
                        combos.append((place_id, sound_id, obstacle_id, gear_id))
    return combos


def explain_sound_rejection(place: Place, sound: SoundClue) -> str:
    return (
        f"(No story: {sound.label} is not a believable exit clue inside the {place.label}. "
        f"This world only allows clue sounds that could really carry there.)"
    )


def explain_gear_rejection(obstacle: Obstacle, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} does not solve the {obstacle.label}. "
        f"The obstacle needs {obstacle.need}, so the gear must truly help.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.trait in {"careful", "thoughtful", "steady", "patient"} and params.urgency <= 1:
        return "quick_exit"
    return "detour_exit"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_exit(world: World, obstacle: Obstacle, gear: Gear, outcome: str) -> dict:
    sim = world.copy()
    sim.facts["took_detour"] = outcome == "detour_exit"
    if sim.facts["took_detour"]:
        sim.get("hero").meters["warning"] += 1
        sim.get("friend").meters["warning"] += 1
    propagate(sim, narrate=False)
    can_cross = gear_matches(obstacle, gear)
    return {
        "detour": sim.facts["took_detour"],
        "fear": sim.get("hero").memes["fear"] + sim.get("friend").memes["fear"],
        "can_cross": can_cross,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, guardian: Entity, place: Place, gear: Gear) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {friend.id} were on an adventure walk with {hero.pronoun('possessive')} "
        f"{guardian.label_word} when they found {place.opening}."
    )
    world.say(
        f"In {hero.id}'s pocket was {gear.phrase}, because adventures always felt better with one useful thing to carry."
    )
    world.say(
        f"They spotted {place.treasure}, and that was enough to pull them a little farther in."
    )


def foreshadow(world: World, hero: Entity, place: Place) -> None:
    world.say(place.warning)
    world.say(
        f'{hero.id} felt a small shiver of thought: "If this place keeps changing, we should remember the way back."'
    )


def find_treasure(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["treasure"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"When {hero.id} reached the shelf, {hero.pronoun()} lifted the little prize and grinned."
    )
    world.say(
        f'"We found it!" {friend.id} whispered, though even the whisper seemed to bounce around the stone.'
    )


def hear_clue(world: World, hero: Entity, friend: Entity, sound: SoundClue) -> None:
    hero.meters["heard_clue"] += 1
    friend.meters["heard_clue"] += 1
    world.say(
        f"Then came the characteristic sound. {sound.effect} It slipped through the shadows from somewhere ahead."
    )
    world.say(
        f'{hero.id} held still. "{sound.hint}" {hero.pronoun()} thought.'
    )


def choose_path(world: World, hero: Entity, friend: Entity, outcome: str, sound: SoundClue) -> None:
    if outcome == "quick_exit":
        hero.memes["confidence"] += 1
        world.say(
            f'"That sound is telling us something," {hero.id} said. "Let\'s follow it."'
        )
        world.say(
            f"{friend.id} nodded at once, and together they turned toward the {sound.label} instead of the darker tunnel."
        )
    else:
        world.facts["took_detour"] = True
        hero.meters["warning"] += 1
        friend.meters["warning"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{hero.id} glanced at one passage, then another. "Maybe the quiet one is shorter," {hero.pronoun()} thought.'
        )
        world.say(
            f"They tried the wrong way first. Crunch-crunch went loose grit under their shoes, and the air there felt close and stale."
        )
        world.say(
            f'"No," {friend.id} said softly. "The good way is where the sound lives."'
        )


def face_obstacle(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Soon they reached {obstacle.scene}. {obstacle.danger}"
    )
    hero.memes["resolve"] += 1
    friend.memes["resolve"] += 1


def use_gear(world: World, hero: Entity, gear: Gear, obstacle: Obstacle) -> None:
    world.facts["used_gear"] = True
    hero.meters["used_tool"] += 1
    world.say(
        f"{hero.id} gripped {gear.phrase}, used it, and {obstacle.fix_text}."
    )


def find_exit(world: World, hero: Entity, friend: Entity, place: Place, sound: SoundClue, outcome: str) -> None:
    world.facts["exit_found"] = True
    hero.meters["safe"] += 1
    friend.meters["safe"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    if outcome == "quick_exit":
        world.say(
            f"Right after that, the clue grew stronger -- {sound.effect} -- and daylight brushed their faces."
        )
    else:
        world.say(
            f"Now the clue was easy to trust. {sound.effect} came clearer, and a ribbon of daylight waited ahead."
        )
    world.say(
        f"They hurried to {place.exit_kind} and slipped out into bright air."
    )


def resolution(world: World, hero: Entity, friend: Entity, guardian: Entity, place: Place, outcome: str) -> None:
    guardian.memes["relief"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} was waiting just outside, worried for one moment and smiling the next."
    )
    if outcome == "quick_exit":
        world.say(
            f'{hero.id} held up the tiny treasure and laughed. "We listened the first time," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} hugged the prize close and admitted, "The sound knew more than I did."'
        )
    world.say(
        f"Behind them, the {place.label} kept its secrets, but the children had learned one useful adventure rule: sometimes the way to the exit begins as a sound before it becomes a sight."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    sound: SoundClue,
    obstacle: Obstacle,
    gear: Gear,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Finn",
    friend_gender: str = "boy",
    guardian_type: str = "mother",
    trait: str = "careful",
    urgency: int = 1,
) -> World:
    world = World(place=place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=["loyal"]))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_type, label="the guardian", role="guardian"))
    world.add(Entity(id="room", kind="thing", type="place", label=place.label))

    world.facts.update(
        exit_found=False,
        took_detour=False,
        used_gear=False,
        urgency=urgency,
    )

    outcome = "quick_exit" if trait in {"careful", "thoughtful", "steady", "patient"} and urgency <= 1 else "detour_exit"

    introduce(world, hero, friend, guardian, place, gear)
    foreshadow(world, hero, place)

    world.para()
    find_treasure(world, hero, friend)
    hear_clue(world, hero, friend, sound)
    choose_path(world, hero, friend, outcome, sound)

    if urgency >= 2:
        hero.meters["warning"] += 1
        friend.meters["warning"] += 1
        propagate(world, narrate=False)

    world.para()
    face_obstacle(world, hero, friend, obstacle)
    use_gear(world, hero, gear, obstacle)
    find_exit(world, hero, friend, place, sound, outcome)

    world.para()
    resolution(world, hero, friend, guardian, place, outcome)

    world.facts.update(
        hero=hero,
        friend=friend,
        guardian=guardian,
        place_cfg=place,
        sound_cfg=sound,
        obstacle_cfg=obstacle,
        gear_cfg=gear,
        outcome=outcome,
        heard_clue=hero.meters["heard_clue"] >= THRESHOLD,
        safe=hero.meters["safe"] >= THRESHOLD and friend.meters["safe"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "waves": [
        (
            "Why can waves help someone find an exit near the sea?",
            "Waves make a steady sound that often comes from open water. If you hear them getting clearer, you may be moving toward the shore and fresh air."
        )
    ],
    "wind": [
        (
            "Why can wind make a clue sound in a cave or tunnel?",
            "Wind whistles when it squeezes through cracks and narrow openings. That can tell you there is a hole or exit nearby."
        )
    ],
    "drip": [
        (
            "Why does dripping water make a regular sound?",
            "Dripping water falls one drop at a time, so it can make a repeated plink sound. Regular sounds are easier to notice and follow."
        )
    ],
    "birds": [
        (
            "Why can bird calls mean the outside is close?",
            "Birds usually call where there is open sky, branches, or ledges. Hearing them inside a ruin can hint that an outside opening is nearby."
        )
    ],
    "light": [
        (
            "Why is a lantern useful in a dark place?",
            "A lantern helps you see the floor, walls, and edges around you. Seeing clearly makes walking much safer."
        )
    ],
    "boots": [
        (
            "Why do grip boots help on slippery stone?",
            "Grip boots hold onto the ground better than smooth shoes. That extra grip helps stop slips."
        )
    ],
    "hook": [
        (
            "What is a hook pole good for?",
            "A hook pole helps you pull or lift something that is too far away for your hand. It lets you reach safely without climbing."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small hint that something important will happen later. It helps the story feel connected when the later event arrives."
        )
    ],
    "inner": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet thought a character says inside their own mind. It lets readers know what the character is thinking."
        )
    ],
    "sound": [
        (
            "What is a characteristic sound?",
            "A characteristic sound is a sound that is easy to recognize because it has a special pattern. That makes it a useful clue."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound", "waves", "wind", "drip", "birds", "light", "boots", "hook", "foreshadowing", "inner"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place_cfg"]
    sound = f["sound_cfg"]
    obstacle = f["obstacle_cfg"]
    gear = f["gear_cfg"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "exit" and "characteristic" and uses sound effects, foreshadowing, and inner monologue.',
        f"Tell an adventure about {hero.label} and {friend.label} exploring a {place.label}, hearing the characteristic sound of {sound.label}, and using {gear.label} to get past a {obstacle.label}.",
        f'Write a gentle adventure where a clue begins as a sound effect, becomes a smart thought inside a child\'s mind, and leads to a safe exit.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian"]
    place = f["place_cfg"]
    sound = f["sound_cfg"]
    obstacle = f["obstacle_cfg"]
    gear = f["gear_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two children on a small adventure, and {hero.pronoun('possessive')} {guardian.label_word} waiting outside. They explore the {place.label} and try to get back out safely."
        ),
        (
            "What clue helped them find the exit?",
            f"The clue was the characteristic sound of {sound.label}: {sound.effect} {sound.hint} That sound mattered because it pointed them toward open air instead of deeper trouble."
        ),
        (
            f"Why did {hero.label} need the {gear.label}?",
            f"{hero.label} needed the {gear.label} because they reached {obstacle.scene}. The tool helped with the exact problem there, so they could keep moving safely."
        ),
    ]
    if outcome == "quick_exit":
        qa.append(
            (
                f"How did {hero.label} make the right choice?",
                f"{hero.label} trusted the clue sound right away and followed it instead of the darker path. That quick choice saved time and kept the adventure from becoming scarier."
            )
        )
    else:
        qa.append(
            (
                f"What mistake did {hero.label} make, and what changed?",
                f"{hero.label} tried the wrong passage first because the quiet path looked tempting. Then {friend.label} reminded {hero.pronoun('object')} to trust the sound, and that changed the choice that led them out."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They reached the exit, stepped into bright air, and felt relieved. The ending shows they learned that a good clue can begin as a sound before it becomes something they can see."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sound", "foreshadowing", "inner"}
    tags |= set(f["sound_cfg"].tags)
    tags |= set(f["gear_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k in {'exit_found', 'took_detour', 'used_gear', 'outcome', 'urgency'}} }")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% reasonableness gate
sound_fits(P,S) :- place(P), sound(S), carries_in(S,P), place_allows_sound(P,S).
gear_fits(O,G)  :- obstacle(O), gear(G), needs(O,N), grants(G,N).
valid(P,S,O,G)  :- place(P), sound(S), obstacle(O), gear(G), sound_fits(P,S), gear_fits(O,G).

% outcome model
careful_trait(T) :- trait(T), calm(T).
quick_exit :- careful_trait(T), urgency(U), U <= 1.
outcome(quick_exit) :- quick_exit.
outcome(detour_exit) :- not quick_exit.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.sound_tags):
            lines.append(asp.fact("place_allows_sound", pid, sid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        for pid in sorted(sound.carries_in):
            lines.append(asp.fact("carries_in", sid, pid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.need))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for grant in sorted(gear.grants):
            lines.append(asp.fact("grants", gid, grant))
    for tr in ["careful", "thoughtful", "steady", "patient"]:
        lines.append(asp.fact("calm", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("urgency", params.urgency),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="sea_cave",
        sound="waves",
        obstacle="slippery_ledge",
        gear="grip_boots",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        guardian="mother",
        trait="careful",
        urgency=1,
    ),
    StoryParams(
        place="old_mine",
        sound="drip",
        obstacle="dark_turn",
        gear="lantern",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        guardian="father",
        trait="curious",
        urgency=2,
    ),
    StoryParams(
        place="sun_temple",
        sound="birds",
        obstacle="high_grate",
        gear="hook_pole",
        hero_name="Ivy",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        guardian="mother",
        trait="steady",
        urgency=1,
    ),
    StoryParams(
        place="sea_cave",
        sound="wind",
        obstacle="dark_turn",
        gear="lantern",
        hero_name="Kai",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        guardian="father",
        trait="brave",
        urgency=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a clue-sound, a hidden exit, and one useful tool."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--urgency", type=int, choices=[0, 1, 2], help="higher means the children are slower to trust the clue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sound:
        place = PLACES[args.place]
        sound = SOUNDS[args.sound]
        if not sound_fits(place, sound):
            raise StoryError(explain_sound_rejection(place, sound))
    if args.obstacle and args.gear:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEAR[args.gear]
        if not gear_matches(obstacle, gear):
            raise StoryError(explain_gear_rejection(obstacle, gear))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.sound is None or c[1] == args.sound)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.gear is None or c[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sound_id, obstacle_id, gear_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    urgency = args.urgency if args.urgency is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        sound=sound_id,
        obstacle=obstacle_id,
        gear=gear_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        guardian=guardian,
        trait=trait,
        urgency=urgency,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Invalid sound: {params.sound})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.gear not in GEAR:
        raise StoryError(f"(Invalid gear: {params.gear})")

    place = PLACES[params.place]
    sound = SOUNDS[params.sound]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEAR[params.gear]

    if not sound_fits(place, sound):
        raise StoryError(explain_sound_rejection(place, sound))
    if not gear_matches(obstacle, gear):
        raise StoryError(explain_gear_rejection(obstacle, gear))

    world = tell(
        place=place,
        sound=sound,
        obstacle=obstacle,
        gear=gear,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        guardian_type=params.guardian,
        trait=params.trait,
        urgency=params.urgency,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, obstacle, gear) combos:\n")
        for place, sound, obstacle, gear in combos:
            print(f"  {place:10} {sound:6} {obstacle:15} {gear}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.place}, {p.sound}, {p.obstacle}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
