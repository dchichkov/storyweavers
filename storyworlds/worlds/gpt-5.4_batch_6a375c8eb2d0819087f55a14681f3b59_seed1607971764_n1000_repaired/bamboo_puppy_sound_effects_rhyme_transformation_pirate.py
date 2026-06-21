#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py
====================================================================================

A standalone story world about a pirate game that goes wrong with a loud noise,
then turns gentle and musical. A puppy is frightened by booming pretend-pirate
sound effects, hides away, and only returns when the children transform the game
with a bamboo tune, a rhyming call, and a little pirate costume.

Run it
------
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py --setting beach_cove --scare toy_cannon --hideout bamboo_patch
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py --response boom_again
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py --all
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bamboo_puppy_sound_effects_rhyme_transformation_pirate.py --verify
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
STARTLE_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        dog = {"puppy", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    frame: str
    rig: str
    quest: str
    path: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class ScareSound:
    id: str
    label: str
    boom: str
    line: str
    loudness: int
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
class Hideout:
    id: str
    label: str
    phrase: str
    peek: str
    sheltered: bool = True
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
    label: str
    sense: int
    power: int
    sound: str
    rhyme: str
    action: str
    qa_text: str
    gives_bandana: bool = True
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


SETTINGS = {
    "beach_cove": Setting(
        id="beach_cove",
        place="the windy cove",
        frame="a salt-bright pirate cove",
        rig="A laundry basket was the ship, a mop became the mast, and a towel on the grass was their treasure map.",
        quest="the shell chest at the far end of the cove",
        path="a chalk plank from one flowerpot to another",
        affords={"bamboo_patch", "net_crate"},
    ),
    "backyard_deck": Setting(
        id="backyard_deck",
        place="the backyard deck",
        frame="a brave pirate deck",
        rig="A cardboard box was the captain's cabin, a broom was the mast, and blue chalk waves curled around the stepping stones.",
        quest="the button treasure by the upside-down bucket",
        path="a rope line between two cushions",
        affords={"bamboo_patch", "under_bench"},
    ),
    "attic_ship": Setting(
        id="attic_ship",
        place="the attic playroom",
        frame="a dusty pirate ship",
        rig="A blanket over two chairs made the stern, a ribbon became the sail, and an old scarf pointed toward hidden gold.",
        quest="the shiny marble chest near the trunk",
        path="a line of pillows across the floorboards",
        affords={"net_crate", "under_bench"},
    ),
}

SCARE_SOUNDS = {
    "drum": ScareSound(
        id="drum",
        label="drum",
        boom="Boom-boom! Dum-da-dum!",
        line="thumped the little drum for a pirate launch",
        loudness=2,
        tags={"drum", "loud_sound"},
    ),
    "pan_lid": ScareSound(
        id="pan_lid",
        label="pan lid",
        boom="Clang-clang! Bang-a-clang!",
        line="smacked a spoon on a pan lid like a brass pirate bell",
        loudness=3,
        tags={"pan", "loud_sound"},
    ),
    "toy_cannon": ScareSound(
        id="toy_cannon",
        label="toy cannon",
        boom="BOOM! Puff! BOOM!",
        line="set off the spring toy cannon again and again",
        loudness=4,
        tags={"cannon", "loud_sound"},
    ),
    "whisper": ScareSound(
        id="whisper",
        label="whisper",
        boom="psst-psst",
        line="whispered so softly that nobody could even call it a launch",
        loudness=0,
        tags={"quiet"},
    ),
}

HIDEOUTS = {
    "bamboo_patch": Hideout(
        id="bamboo_patch",
        label="bamboo patch",
        phrase="a little patch of bamboo by the fence",
        peek="two round eyes blinked between the bamboo leaves",
        sheltered=True,
        tags={"bamboo", "hide"},
    ),
    "net_crate": Hideout(
        id="net_crate",
        label="net crate",
        phrase="the old net crate with the folded beach towels",
        peek="a black nose poked out through the rope loops",
        sheltered=True,
        tags={"crate", "hide"},
    ),
    "under_bench": Hideout(
        id="under_bench",
        label="bench shadow",
        phrase="the shadow under the wooden bench",
        peek="a wag-less tail tip twitched in the dark",
        sheltered=True,
        tags={"bench", "hide"},
    ),
    "open_mat": Hideout(
        id="open_mat",
        label="open mat",
        phrase="the open mat in the middle of the floor",
        peek="nothing hid there at all",
        sheltered=False,
        tags={"open"},
    ),
}

RESPONSES = {
    "bamboo_flute": Response(
        id="bamboo_flute",
        label="bamboo flute",
        sense=3,
        power=3,
        sound="Toot-toot, too-loo!",
        rhyme='"Soft pirate, bright pirate, come with me. Small paws, brave cause, over the sea."',
        action="lifted a little bamboo flute and played a soft tune while tying a tiny red bandana around the puppy's neck",
        qa_text="played a soft bamboo tune and tied on a little pirate bandana",
        gives_bandana=True,
        tags={"bamboo", "music", "rhyme", "bandana"},
    ),
    "bamboo_pipes": Response(
        id="bamboo_pipes",
        label="bamboo pipes",
        sense=3,
        power=4,
        sound="Poo-woo! Poo-woo!",
        rhyme='"Pipes low, tails go; pipes sweet, small paws meet."',
        action="blew across the bamboo pipes in a low song and draped a striped scarf over the puppy like a captain's sash",
        qa_text="played low bamboo pipes and wrapped the puppy in a striped pirate sash",
        gives_bandana=True,
        tags={"bamboo", "music", "rhyme", "scarf"},
    ),
    "biscuit_rhyme": Response(
        id="biscuit_rhyme",
        label="biscuit rhyme",
        sense=2,
        power=2,
        sound="Tap-tap. Pat-pat.",
        rhyme='"Pup-pup, cheer up, here is your treat. Step by step, bring your brave feet."',
        action="patted the floor in a slow beat, sang a biscuit rhyme, and held out one crunchy treat",
        qa_text="used a gentle rhyme and a crunchy treat to coax the puppy out",
        gives_bandana=False,
        tags={"rhyme", "treat", "gentle"},
    ),
    "boom_again": Response(
        id="boom_again",
        label="more booming",
        sense=1,
        power=0,
        sound="BOOM-BOOM!",
        rhyme='"Boom and zoom!"',
        action="made the pirate noise even louder and hoped the puppy would get used to it",
        qa_text="made the noise louder",
        gives_bandana=False,
        tags={"loud_sound"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Lucy", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]
TRAITS = ["careful", "cheerful", "gentle", "curious", "thoughtful", "steady"]
PUPPY_NAMES = ["Pebble", "Biscuit", "Pip", "Sailor", "Moss"]


@dataclass
class StoryParams:
    setting: str
    scare: str
    hideout: str
    response: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    puppy_name: str
    parent: str
    trait: str
    delay: int = 0
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
        setting="beach_cove",
        scare="drum",
        hideout="bamboo_patch",
        response="bamboo_flute",
        child_a="Tom",
        child_a_gender="boy",
        child_b="Lily",
        child_b_gender="girl",
        puppy_name="Pebble",
        parent="mother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        setting="backyard_deck",
        scare="pan_lid",
        hideout="under_bench",
        response="bamboo_pipes",
        child_a="Ava",
        child_a_gender="girl",
        child_b="Ben",
        child_b_gender="boy",
        puppy_name="Biscuit",
        parent="father",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        setting="attic_ship",
        scare="toy_cannon",
        hideout="net_crate",
        response="bamboo_flute",
        child_a="Max",
        child_a_gender="boy",
        child_b="Nora",
        child_b_gender="girl",
        puppy_name="Pip",
        parent="mother",
        trait="careful",
        delay=2,
    ),
    StoryParams(
        setting="beach_cove",
        scare="pan_lid",
        hideout="bamboo_patch",
        response="biscuit_rhyme",
        child_a="Lucy",
        child_a_gender="girl",
        child_b="Sam",
        child_b_gender="boy",
        puppy_name="Sailor",
        parent="father",
        trait="steady",
        delay=1,
    ),
]


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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_hide(world: World) -> list[str]:
    puppy = world.get("puppy")
    out: list[str] = []
    if puppy.meters["fear"] >= THRESHOLD:
        sig = ("hide", puppy.id)
        if sig not in world.fired:
            world.fired.add(sig)
            puppy.meters["hidden"] += 1
            world.get("game").meters["stalled"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__hide__")
    return out


def _r_emerge(world: World) -> list[str]:
    puppy = world.get("puppy")
    if puppy.meters["hidden"] < THRESHOLD:
        return []
    if puppy.memes["calm"] < THRESHOLD and puppy.memes["bravery"] < THRESHOLD:
        return []
    sig = ("emerge", puppy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    puppy.meters["hidden"] = 0.0
    puppy.meters["found"] += 1
    world.get("game").meters["stalled"] = 0.0
    puppy.memes["fear"] = 0.0
    puppy.memes["join"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    return ["__emerge__"]


def _r_transform(world: World) -> list[str]:
    puppy = world.get("puppy")
    if puppy.meters["costumed"] < THRESHOLD or puppy.meters["found"] < THRESHOLD:
        return []
    sig = ("transform", puppy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    puppy.meters["transformed"] += 1
    puppy.memes["pride"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="hide", tag="physical", apply=_r_hide),
    Rule(name="emerge", tag="social", apply=_r_emerge),
    Rule(name="transform", tag="social", apply=_r_transform),
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
        for line in produced:
            world.say(line)
    return produced


def startling(scare: ScareSound) -> bool:
    return scare.loudness >= STARTLE_MIN


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for scare_id, scare in SCARE_SOUNDS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if startling(scare) and hideout.sheltered and hideout_id in setting.affords:
                    combos.append((setting_id, scare_id, hideout_id))
    return combos


def scare_severity(scare: ScareSound, delay: int) -> int:
    return scare.loudness + delay


def is_calmed(response: Response, scare: ScareSound, delay: int) -> bool:
    return response.power >= scare_severity(scare, delay)


def explain_combo_rejection(setting: Setting, scare: ScareSound, hideout: Hideout) -> str:
    if not startling(scare):
        return (
            f"(No story: {scare.label} is too quiet to startle the puppy, so there is no hiding turn. "
            f"Choose a louder pirate sound like a drum, a pan lid, or a toy cannon.)"
        )
    if not hideout.sheltered:
        return (
            f"(No story: {hideout.phrase} is not really a hiding place, so the puppy would not vanish there. "
            f"Pick a sheltered place like bamboo, a crate, or under a bench.)"
        )
    if hideout.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not plausibly include {hideout.phrase}. "
            f"Pick a hideout that belongs in that setting.)"
        )
    return "(No story: that combination does not make a reasonable frightened-puppy tale.)"


def explain_response_rejection(response: Response) -> str:
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response.id}': it is not a gentle fix for a frightened puppy. "
        f"Try one of these instead: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.scare not in SCARE_SOUNDS or params.response not in RESPONSES:
        raise StoryError("(No story: unknown scare or response id.)")
    return "calmed" if is_calmed(RESPONSES[params.response], SCARE_SOUNDS[params.scare], params.delay) else "late"


def _do_scare(world: World, scare: ScareSound, narrate: bool = True) -> None:
    puppy = world.get("puppy")
    puppy.meters["startled"] += 1
    puppy.meters["fear"] += 1
    puppy.memes["trust"] = max(0.0, puppy.memes["trust"] - 1.0)
    propagate(world, narrate=narrate)


def _do_soothe(world: World, response: Response, narrate: bool = True) -> None:
    puppy = world.get("puppy")
    puppy.memes["calm"] += 1
    puppy.memes["bravery"] += 1
    if response.gives_bandana:
        puppy.meters["costumed"] += 1
    propagate(world, narrate=narrate)


def predict_hidden(world: World, scare: ScareSound) -> dict:
    sim = world.copy()
    _do_scare(sim, scare, narrate=False)
    puppy = sim.get("puppy")
    return {
        "hidden": puppy.meters["hidden"] >= THRESHOLD,
        "stalled": sim.get("game").meters["stalled"],
    }


def setup_scene(world: World, a: Entity, b: Entity, puppy: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    puppy.memes["trust"] += 2
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned {setting.place} into {setting.frame}. "
        f"{setting.rig}"
    )
    world.say(
        f'Their puppy, {puppy.id}, bounced after them with a shoelace in {puppy.pronoun("possessive")} mouth, '
        f"certain that any pirate game should include a puppy."
    )
    world.say(
        f'"Captain {a.id} and First Mate {b.id}!" {a.id} cried. "Today we sail for {setting.quest} by way of {setting.path}."'
    )


def launch_noise(world: World, a: Entity, scare: ScareSound) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'To start the voyage, {a.id} {scare.line}. "{scare.boom}" rang across the game.'
    )
    _do_scare(world, scare, narrate=False)


def hide_beat(world: World, puppy: Entity, hideout: Hideout) -> None:
    if puppy.meters["hidden"] >= THRESHOLD:
        world.say(
            f"The sound was too big for a little puppy. {puppy.id} tucked {puppy.pronoun('possessive')} tail, skidded away, and vanished into {hideout.phrase}."
        )
        world.say(f"Soon the ship felt empty. {hideout.peek}.")


def warn(world: World, b: Entity, scare: ScareSound) -> None:
    pred = predict_hidden(world, scare)
    world.facts["predicted_hidden"] = pred["hidden"]
    world.facts["predicted_stalled"] = pred["stalled"]
    b.memes["care"] += 1
    world.say(
        f'{b.id} stopped at once. "No more booming," {b.pronoun()} said. "When the pirate sound gets that loud, our puppy thinks the game is scary instead of fun."'
    )


def choose_gentle_plan(world: World, parent: Entity, response: Response) -> None:
    world.say(
        f'{parent.label_word.capitalize()} knelt beside the ship and spoke softly. "A brave pirate does not drag a frightened friend. A brave pirate changes the plan."'
    )
    world.say(
        f'{parent.pronoun().capitalize()} reached for the {response.label}. "{response.sound}" {parent.pronoun()} tried, small and slow.'
    )
    world.say(response.rhyme)


def soothe_success(world: World, parent: Entity, puppy: Entity, response: Response, setting: Setting) -> None:
    _do_soothe(world, response, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} {response.action}."
    )
    world.say(
        f"{puppy.id} listened. First one ear lifted, then the other. At last {puppy.pronoun()} stepped out from hiding and padded toward {setting.path}."
    )


def soothe_late(world: World, parent: Entity, puppy: Entity, response: Response, setting: Setting) -> None:
    puppy.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.action}."
    )
    world.say(
        f"{puppy.id} stopped shaking, but {puppy.pronoun()} stayed deep in the hiding place while the afternoon light grew gold."
    )
    world.say(
        f'"We scared our puppy too much for today," {parent.label_word} said. "So today the bravest thing is to end the raid gently and begin again tomorrow."'
    )
    puppy.memes["trust"] += 1
    world.get("game").meters["stalled"] = 1.0


def transform_puppy(world: World, puppy: Entity) -> None:
    if puppy.meters["transformed"] >= THRESHOLD:
        world.say(
            f"The tiny costume changed everything in the pirate game. In one delighted blink, {puppy.id} was no longer just the puppy under the table or behind the bamboo. {puppy.pronoun().capitalize()} had become Captain Barkbeard, the boldest little sea dog on deck."
        )


def ending_happy(world: World, a: Entity, b: Entity, puppy: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    puppy.memes["joy"] += 1
    world.say(
        f'Soon {a.id}, {b.id}, and {puppy.id} crossed {setting.path} together. Tap-tap went the feet, pat-pat went the paws, and the whole pirate ship moved to the soft bamboo tune.'
    )
    world.say(
        f'When they reached {setting.quest}, {b.id} laughed. "The treasure was not only the shell chest," {b.pronoun()} said. "It was bringing our puppy back."'
    )
    world.say(
        f"And that is how the loud pirate raid became a gentle pirate parade, with bamboo music in the air and a brave little puppy trotting at the front."
    )


def ending_late(world: World, a: Entity, b: Entity, puppy: Entity, response: Response, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
    world.say(
        f"So the treasure map stayed folded, and the children sat by {hide_phrase(world)} while {response.sound.lower()} faded into the evening."
    )
    world.say(
        f"The next morning they began again with a gentle bamboo sound instead of a boom, and this time their puppy came out at once."
    )
    world.say(
        f"From then on, their pirate games started softly, because even pirates had learned how to make room for a small, brave puppy."
    )


def hide_phrase(world: World) -> str:
    hideout = world.facts["hideout_cfg"]
    return hideout.phrase


def tell(
    setting: Setting,
    scare: ScareSound,
    hideout: Hideout,
    response: Response,
    child_a: str = "Tom",
    child_a_gender: str = "boy",
    child_b: str = "Lily",
    child_b_gender: str = "girl",
    puppy_name: str = "Pebble",
    parent_type: str = "mother",
    trait: str = "gentle",
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=child_a_gender, role="captain", traits=["bold"]))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_gender, role="mate", traits=[trait]))
    puppy = world.add(Entity(id=puppy_name, kind="character", type="puppy", role="puppy", traits=["small", "wriggly"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="game", type="game", label="the pirate game"))
    world.add(Entity(id="hideout", type="hideout", label=hideout.label, attrs={"phrase": hideout.phrase}))

    world.facts.update(
        setting=setting,
        scare_cfg=scare,
        hideout_cfg=hideout,
        response_cfg=response,
        delay=delay,
        child_a=a,
        child_b=b,
        puppy=puppy,
        parent=parent,
    )

    setup_scene(world, a, b, puppy, setting)

    world.para()
    launch_noise(world, a, scare)
    propagate(world, narrate=False)
    hide_beat(world, puppy, hideout)
    warn(world, b, scare)

    world.para()
    choose_gentle_plan(world, parent, response)

    if is_calmed(response, scare, delay):
        soothe_success(world, parent, puppy, response, setting)
        propagate(world, narrate=False)
        transform_puppy(world, puppy)
        world.para()
        ending_happy(world, a, b, puppy, setting)
        outcome = "calmed"
    else:
        soothe_late(world, parent, puppy, response, setting)
        world.para()
        ending_late(world, a, b, puppy, response, setting)
        outcome = "late"

    world.facts.update(
        outcome=outcome,
        transformed=puppy.meters["transformed"] >= THRESHOLD,
        hidden=puppy.meters["hidden"] >= THRESHOLD,
        joined=puppy.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bamboo": [
        (
            "What is bamboo?",
            "Bamboo is a tall, hollow plant with smooth stems. People can use bamboo to make light things like pipes, little flutes, or garden poles.",
        )
    ],
    "music": [
        (
            "Why can soft music help a puppy feel calm?",
            "Soft music is gentle and steady, so it does not feel like a threat. A puppy can listen, slow down, and decide that the place is safe again.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching sounds, like low and go. Rhymes can make a song easy to remember and soft to repeat.",
        )
    ],
    "puppy": [
        (
            "Why might a puppy hide from a loud sound?",
            "A puppy has sharp ears, so a sudden loud sound can feel scary. Hiding is one way a puppy tries to feel safe again.",
        )
    ],
    "bandana": [
        (
            "What is a bandana?",
            "A bandana is a small cloth you can tie around a neck or head. In a pretend pirate game, it can look like a tiny costume.",
        )
    ],
    "drum": [
        (
            "What sound does a drum make?",
            "A drum makes deep thumping sounds, like boom-boom or dum-dum. Loud drum sounds can travel a long way.",
        )
    ],
    "cannon": [
        (
            "Why is a pretend cannon still scary to a puppy?",
            "Even a toy cannon can make a sharp popping or booming sound. A puppy does not always know it is only part of a game.",
        )
    ],
    "gentle": [
        (
            "What does it mean to be gentle with an animal?",
            "Being gentle means moving softly, sounding calm, and giving the animal space. It helps the animal trust you.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bamboo", "puppy", "music", "rhyme", "bandana", "drum", "cannon", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    puppy = f["puppy"]
    setting = f["setting"]
    scare = f["scare_cfg"]
    response = f["response_cfg"]
    if f["outcome"] == "calmed":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "bamboo" and "puppy", uses sound effects and a rhyme, and ends with a frightened puppy joining the game.',
            f"Tell a gentle pirate tale where {a.id} and {b.id} make too much noise, frighten their puppy, and then use {response.label} to change the whole game into something soft and kind.",
            f"Write a story where a pirate game starts with {scare.label} noises but transforms into a bamboo music parade, and the puppy becomes the brave first mate.",
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "bamboo" and "puppy", uses sound effects and a rhyme, and shows children learning to start more gently next time.',
        f"Tell a pirate tale where {a.id} and {b.id} scare {puppy.id} with {scare.label} noises, try to fix it, and learn that a frightened puppy may need more time than a game does.",
        f"Write a story where the children cannot finish the treasure hunt that day, but the pirate game still changes by the end because they choose a softer bamboo sound for tomorrow.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    puppy = f["puppy"]
    parent = f["parent"]
    setting = f["setting"]
    scare = f["scare_cfg"]
    hideout = f["hideout_cfg"]
    response = f["response_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, who are pretending to be pirates, and their puppy, {puppy.id}. Their {parent.label_word} helps when the game stops feeling fun for the puppy.",
        ),
        (
            "What problem happened in the pirate game?",
            f"The pirate launch was too loud, so the puppy got scared and hid in {hideout.phrase}. That changed the game right away, because the children wanted their puppy with them.",
        ),
        (
            f"Why did {b.id} say there should be no more booming?",
            f"{b.id} saw that the loud {scare.label} sound had frightened the puppy. {b.pronoun().capitalize()} understood that a game is not brave if one small friend feels unsafe inside it.",
        ),
    ]
    if f["outcome"] == "calmed":
        qa.extend(
            [
                (
                    f"How did they help {puppy.id} come back?",
                    f"They used {response.label} instead of more booming. The soft sound and the rhyme helped the puppy calm down, and the little pirate costume made the game feel friendly again.",
                ),
                (
                    f"What transformation happened in the story?",
                    f"The game changed from a noisy raid into a gentle parade, and the puppy changed from a frightened hider into a proud pirate helper. That transformation showed that kindness can change the whole feeling of play.",
                ),
                (
                    "How did the story end?",
                    f"It ended with the children, the puppy, and the bamboo music moving together toward the treasure. The ending image proves what changed, because the puppy was no longer hiding and was leading the adventure instead.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Did {puppy.id} come out right away?",
                    f"No. The puppy calmed a little, but the scare from the loud sound was still too big for that day. The children had to stop the raid and learn to begin more gently next time.",
                ),
                (
                    "What transformation still happened, even though the treasure hunt stopped?",
                    f"The children changed their idea of what a good pirate game should sound like. By the end, they cared more about making room for their puppy than about finishing the treasure first.",
                ),
                (
                    "How did the story end?",
                    f"It ended quietly, with the map folded and the lesson remembered. The next day they began with a softer bamboo sound, showing that the real change was in how they played.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scare = f["scare_cfg"]
    response = f["response_cfg"]
    tags = {"puppy", "gentle"}
    tags |= set(response.tags)
    if "drum" in scare.tags:
        tags.add("drum")
    if "cannon" in scare.tags:
        tags.add("cannon")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
startling(S) :- scare(S), loudness(S,L), startle_min(M), L >= M.
sensible(R)  :- response(R), sense(R,S), sense_min(M), S >= M.

valid(St, Sc, H) :- setting(St), scare(Sc), hideout(H),
                    startling(Sc), sheltered(H), affords(St, H).

severity(L + D) :- chosen_scare(S), loudness(S, L), delay(D).
calmed          :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(calmed) :- calmed.
outcome(late)   :- not calmed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for hideout_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, hideout_id))
    for scare_id, scare in SCARE_SOUNDS.items():
        lines.append(asp.fact("scare", scare_id))
        lines.append(asp.fact("loudness", scare_id, scare.loudness))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        if hideout.sheltered:
            lines.append(asp.fact("sheltered", hideout_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("startle_min", STARTLE_MIN))
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
            asp.fact("chosen_scare", params.scare),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(clingo_sense))
        print("  python:", sorted(python_sense))

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test generated incomplete sample")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="SMOKE")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate game, a frightened puppy, and a gentle bamboo transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scare", choices=SCARE_SOUNDS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the fright lingers before the gentle fix reaches the puppy")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(RESPONSES[args.response]))

    if args.setting and args.scare and args.hideout:
        setting = SETTINGS[args.setting]
        scare = SCARE_SOUNDS[args.scare]
        hideout = HIDEOUTS[args.hideout]
        combo = (args.setting, args.scare, args.hideout)
        if combo not in set(valid_combos()):
            raise StoryError(explain_combo_rejection(setting, scare, hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.scare is None or combo[1] == args.scare)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, scare_id, hideout_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_a, child_a_gender = _pick_child(rng)
    child_b, child_b_gender = _pick_child(rng, avoid=child_a)
    puppy_name = rng.choice(PUPPY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        scare=scare_id,
        hideout=hideout_id,
        response=response_id,
        child_a=child_a,
        child_a_gender=child_a_gender,
        child_b=child_b,
        child_b_gender=child_b_gender,
        puppy_name=puppy_name,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.scare not in SCARE_SOUNDS:
        raise StoryError(f"(No story: unknown scare '{params.scare}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    setting = SETTINGS[params.setting]
    scare = SCARE_SOUNDS[params.scare]
    hideout = HIDEOUTS[params.hideout]
    response = RESPONSES[params.response]
    if (params.setting, params.scare, params.hideout) not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(setting, scare, hideout))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(response))

    world = tell(
        setting=setting,
        scare=scare,
        hideout=hideout,
        response=response,
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        puppy_name=params.puppy_name,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, scare, hideout) combos:\n")
        for setting, scare, hideout in combos:
            print(f"  {setting:12} {scare:10} {hideout}")
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
            header = f"### {p.child_a}, {p.child_b}, and {p.puppy_name}: {p.scare} -> {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
