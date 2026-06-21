#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py
===============================================================

A standalone story world about a child space captain who mistakes a tiny funny
thing for a giant alien because of perspective. The world simulates the visual
mix-up, a possible goofy overreaction, and the calm fix that changes the ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py --setting moonwalk --object sticker_star
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py --fix laser
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/perspective_humor_space_adventure.py --verify
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
JITTERY_TRAITS = {"jumpy", "dramatic", "nervous"}


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
    place: str
    surface: str
    backdrop: str
    launch: str
    path: str
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
class Mission:
    id: str
    title: str
    goal: str
    need: str
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


@dataclass
class FunnyObject:
    id: str
    label: str
    phrase: str
    tiny_truth: str
    surfaces: set[str]
    arrival: str
    reveal: str
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
class Fix:
    id: str
    sense: int
    surfaces: set[str]
    action: str
    qa_text: str
    final_image: str
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


def _r_perspective(world: World) -> list[str]:
    surface = world.get("surface")
    sight = world.get("sight")
    captain = world.get("captain")
    if surface.meters["occupied"] < THRESHOLD or sight.meters["stuck"] < THRESHOLD:
        return []
    if world.facts.get("surface_kind") not in sight.attrs.get("surfaces", set()):
        return []
    sig = ("perspective", sight.id, world.facts.get("surface_kind"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.meters["misread_size"] += 1
    captain.memes["alarm"] += 1
    sight.meters["looks_giant"] += 1
    return ["__perspective__"]


def _r_foam(world: World) -> list[str]:
    ship = world.get("ship")
    if ship.meters["alarm_button"] < THRESHOLD:
        return []
    sig = ("foam", ship.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["foam"] += 1
    world.get("captain").memes["surprise"] += 1
    world.get("copilot").memes["surprise"] += 1
    return ["__foam__"]


def _r_relief(world: World) -> list[str]:
    captain = world.get("captain")
    sight = world.get("sight")
    if captain.meters["misread_size"] >= THRESHOLD:
        return []
    if sight.meters["revealed_tiny"] < THRESHOLD:
        return []
    sig = ("relief", captain.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["relief"] += 1
    captain.memes["giggle"] += 1
    world.get("copilot").memes["giggle"] += 1
    return []
    

CAUSAL_RULES: list[Rule] = [
    Rule(name="perspective", tag="visual", apply=_r_perspective),
    Rule(name="foam", tag="physical", apply=_r_foam),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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


def valid_combo(setting_id: str, object_id: str, fix_id: str) -> bool:
    if setting_id not in SETTINGS or object_id not in OBJECTS or fix_id not in FIXES:
        return False
    setting = SETTINGS[setting_id]
    funny = OBJECTS[object_id]
    fix = FIXES[fix_id]
    return setting.surface in funny.surfaces and setting.surface in fix.surfaces and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for mission_id in MISSIONS:
            for object_id in OBJECTS:
                for fix_id in FIXES:
                    if valid_combo(setting_id, object_id, fix_id):
                        combos.append((setting_id, mission_id, object_id, fix_id))
    return combos


def would_panic(trait: str) -> bool:
    return trait in JITTERY_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "foamy_laugh" if would_panic(params.trait) else "calm_laugh"


def predict_mixup(world: World) -> dict:
    sim = world.copy()
    sim.get("surface").meters["occupied"] = 1.0
    sim.get("sight").meters["stuck"] = 1.0
    propagate(sim, narrate=False)
    return {
        "misread": sim.get("captain").meters["misread_size"] >= THRESHOLD,
        "alarm": sim.get("captain").memes["alarm"] >= THRESHOLD,
    }


def launch_setup(world: World, captain: Entity, copilot: Entity,
                 setting: Setting, mission: Mission) -> None:
    captain.memes["joy"] += 1
    copilot.memes["joy"] += 1
    world.say(
        f"Captain {captain.id} and Copilot {copilot.id} blasted off from {setting.launch}. "
        f"To them, {setting.place} was a shining stretch of deep space."
    )
    world.say(
        f"Their mission was {mission.title}: {mission.goal}. "
        f"{mission.need}"
    )


def spot_trouble(world: World, captain: Entity, copilot: Entity,
                 setting: Setting, funny: FunnyObject) -> None:
    pred = predict_mixup(world)
    world.facts["predicted_misread"] = pred["misread"]
    world.get("surface").meters["occupied"] = 1.0
    world.get("sight").meters["stuck"] = 1.0
    propagate(world, narrate=False)
    world.say(funny.arrival.format(backdrop=setting.backdrop, path=setting.path))
    if pred["misread"]:
        world.say(
            f'Captain {captain.id} squinted through the {setting.surface} and gasped. '
            f'"A giant alien is blocking {setting.path}!"'
        )
        world.say(
            f'Copilot {copilot.id} tilted {copilot.pronoun("possessive")} head. '
            f'"Maybe it only looks giant from this perspective," {copilot.pronoun()} said.'
        )


def panic_beat(world: World, captain: Entity, copilot: Entity) -> None:
    world.get("ship").meters["alarm_button"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But Captain {captain.id} was already in full rescue mode. "
        f'{captain.pronoun().capitalize()} slapped the silly alarm button.'
    )
    world.say(
        "At once, the rocket's emergency joke-foam popped out of a ceiling tube "
        "and dropped soft white bubbles on everybody's shoulders."
    )
    world.say(
        f'"That is not the serious alarm," said {copilot.id}, wiping foam from '
        f'{copilot.pronoun("possessive")} nose.'
    )


def calm_beat(world: World, captain: Entity, copilot: Entity) -> None:
    captain.memes["trust"] += 1
    world.say(
        f"Captain {captain.id} took one brave breath and listened. "
        f'{captain.pronoun().capitalize()} lowered {captain.pronoun("possessive")} hands and nodded.'
    )
    world.say(
        f'"Okay," said {captain.id}. "Let us test the perspective before we run away."'
    )


def reveal_truth(world: World, captain: Entity, copilot: Entity,
                 setting: Setting, funny: FunnyObject, fix: Fix, mission: Mission) -> None:
    world.get("surface").meters["occupied"] = 0.0
    world.get("sight").meters["stuck"] = 0.0
    world.get("sight").meters["revealed_tiny"] = 1.0
    world.get("captain").meters["misread_size"] = 0.0
    propagate(world, narrate=False)
    world.say(fix.action.format(surface=setting.surface, backdrop=setting.backdrop))
    world.say(
        f"Then the monster vanished. In its place was only {funny.tiny_truth}."
    )
    world.say(funny.reveal)
    world.say(
        f"Captain {captain.id} blinked, then laughed so hard {captain.pronoun()} had to hold the ship rail. "
        f'"It was just perspective!" {captain.pronoun()} said.'
    )
    world.say(
        f"Copilot {copilot.id} laughed too, and together they finished the mission. "
        f"{mission.ending}"
    )
    world.say(fix.final_image)


@dataclass
class StoryParams:
    setting: str
    mission: str
    object: str
    fix: str
    captain: str
    captain_gender: str
    copilot: str
    copilot_gender: str
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


def tell(setting: Setting, mission: Mission, funny: FunnyObject, fix: Fix,
         captain_name: str = "Nova", captain_gender: str = "girl",
         copilot_name: str = "Jett", copilot_gender: str = "boy",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=[trait],
    ))
    copilot = world.add(Entity(
        id=copilot_name,
        kind="character",
        type=copilot_gender,
        role="copilot",
        traits=["steady"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="grownup",
        label="the grown-up",
    ))
    ship = world.add(Entity(id="ship", type="ship", label="rocket"))
    surface = world.add(Entity(id="surface", type="surface", label=setting.surface))
    sight = world.add(Entity(
        id="sight",
        type="funny_thing",
        label=funny.label,
        attrs={"surfaces": set(funny.surfaces)},
    ))

    ship.meters["alarm_button"] = 0.0
    ship.meters["foam"] = 0.0
    surface.meters["occupied"] = 0.0
    sight.meters["stuck"] = 0.0
    sight.meters["revealed_tiny"] = 0.0
    captain.meters["misread_size"] = 0.0
    captain.memes["alarm"] = 0.0
    captain.memes["joy"] = 0.0
    captain.memes["trust"] = 0.0
    captain.memes["relief"] = 0.0
    captain.memes["giggle"] = 0.0
    copilot.memes["joy"] = 0.0
    copilot.memes["giggle"] = 0.0

    world.facts.update(
        setting=setting,
        mission=mission,
        funny=funny,
        fix=fix,
        captain=captain,
        copilot=copilot,
        parent=parent,
        ship=ship,
        surface_kind=setting.surface,
        panic=would_panic(trait),
    )

    launch_setup(world, captain, copilot, setting, mission)
    world.para()
    spot_trouble(world, captain, copilot, setting, funny)
    world.para()
    if would_panic(trait):
        panic_beat(world, captain, copilot)
    else:
        calm_beat(world, captain, copilot)
    world.para()
    reveal_truth(world, captain, copilot, setting, funny, fix, mission)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            mission=mission.id,
            object=funny.id,
            fix=fix.id,
            captain=captain_name,
            captain_gender=captain_gender,
            copilot=copilot_name,
            copilot_gender=copilot_gender,
            parent=parent_type,
            trait=trait,
            seed=None,
        )),
        foam=ship.meters["foam"] >= THRESHOLD,
        learned_perspective=captain.memes["relief"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonwalk": Setting(
        id="moonwalk",
        place="the Moon Loop Plain",
        surface="visor",
        backdrop="a silver crater wall",
        launch="a cardboard moon buggy",
        path="the crater path",
        tags={"moon", "space"},
    ),
    "cockpit": Setting(
        id="cockpit",
        place="the Red Comet cockpit",
        surface="window",
        backdrop="the red hills of Mars",
        launch="their wobbling sofa rocket",
        path="the landing lane",
        tags={"mars", "space"},
    ),
    "station": Setting(
        id="station",
        place="the Ring Station lookout deck",
        surface="dome",
        backdrop="the bright rings of Saturn",
        launch="their blanket-built command pod",
        path="the docking bridge",
        tags={"saturn", "space"},
    ),
}

MISSIONS = {
    "cookie": Mission(
        id="cookie",
        title="Operation Comet Cookie",
        goal="carry a crumbly cookie to the hungry rover on the far side of the base",
        need="If the cookie broke too soon, the rover would only get crumbs and a sad beep.",
        ending="The rover got its cookie and answered with a happy beep-beep.",
        tags={"cookie", "rover"},
    ),
    "flag": Mission(
        id="flag",
        title="Operation Noodle Flag",
        goal="plant a noodle-striped flag on the highest pillow asteroid",
        need="A proper captain always plants the flag before snack time.",
        ending="The noodle flag flapped proudly in the pretend solar wind.",
        tags={"flag", "pillow"},
    ),
    "rescue": Mission(
        id="rescue",
        title="Operation Squeaky Rescue",
        goal="find the squeaky scout robot that had rolled out of sight",
        need="Without it, their map kept pointing at the laundry basket nebula.",
        ending="The squeaky scout robot rolled back with a proud little squeak.",
        tags={"robot", "rescue"},
    ),
}

OBJECTS = {
    "sticker_star": FunnyObject(
        id="sticker_star",
        label="sticker star",
        phrase="a shiny sticker star",
        tiny_truth="a shiny sticker star stuck right on the front",
        surfaces={"visor", "window", "dome"},
        arrival="A shiny blink wobbled across {backdrop}, and from the captain's seat it looked as if something huge had parked itself on {path}.",
        reveal="It had been so close to their eyes that it covered half the view and acted like a giant by accident.",
        tags={"sticker", "perspective"},
    ),
    "snail_blob": FunnyObject(
        id="snail_blob",
        label="snail blob",
        phrase="a tiny jelly snail from the snack box",
        tiny_truth="a tiny jelly snail from the snack box inching across the clear surface",
        surfaces={"window", "dome"},
        arrival="Something squishy slid over {backdrop}, and its wiggly shadow made it seem as if a grand space beast was crawling over {path}.",
        reveal="The jelly snail had been on the clear surface the whole time, looking enormous only because it was much closer than the hills behind it.",
        tags={"snail", "perspective"},
    ),
    "wobble_bot": FunnyObject(
        id="wobble_bot",
        label="wobble bot",
        phrase="a thumb-sized repair bot",
        tiny_truth="a thumb-sized repair bot dangling by one magnet",
        surfaces={"visor", "dome"},
        arrival="A dark shape bobbled over {backdrop}, and every little wiggle made it seem like a huge alien toe-tapping on {path}.",
        reveal="The repair bot was so near that one tiny wobble looked giant against the distant view.",
        tags={"robot", "perspective"},
    ),
}

FIXES = {
    "wipe": Fix(
        id="wipe",
        sense=3,
        surfaces={"visor", "window", "dome"},
        action="So Copilot gently wiped the {surface} with a soft cloth and asked Captain to look again.",
        qa_text="wiped the surface clean and checked again",
        final_image="Soon the little ship rolled on, and two explorers zoomed past the crater laughing at the bravest sticker star in space.",
        tags={"wipe", "look_closer"},
    ),
    "step_sideways": Fix(
        id="step_sideways",
        sense=3,
        surfaces={"visor", "window", "dome"},
        action="So the two space travelers stepped sideways together and looked from a new angle instead of the old one.",
        qa_text="changed their angle and looked from a new place",
        final_image="Soon their boots and wheels bumped onward, and the stars seemed friendlier now that the whole crew trusted a new point of view.",
        tags={"angle", "look_closer"},
    ),
    "lower_visor": Fix(
        id="lower_visor",
        sense=2,
        surfaces={"visor"},
        action="So Captain lifted the visor for one second, and both explorers peeked carefully from a clearer view.",
        qa_text="lifted the visor for a clearer look",
        final_image="Soon the moon buggy bounced ahead again, and Captain saluted the tiny troublemaker before driving on.",
        tags={"visor", "look_closer"},
    ),
    "laser": Fix(
        id="laser",
        sense=1,
        surfaces={"visor", "window", "dome"},
        action="Captain nearly reached for the glitter laser, but that would have been far too silly.",
        qa_text="used a laser",
        final_image="No sensible crew zaps a window before taking a second look.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Zuri", "Ayla", "Poppy", "Ivy"]
BOY_NAMES = ["Jett", "Leo", "Milo", "Orion", "Finn", "Kai", "Nico", "Theo"]
TRAITS = ["curious", "brave", "jumpy", "dramatic", "careful", "nervous"]


KNOWLEDGE = {
    "perspective": [
        (
            "What does perspective mean?",
            "Perspective is how something looks from where you are standing or looking. A tiny thing close to your eyes can seem bigger than a faraway thing."
        ),
    ],
    "space": [
        (
            "Why do things in space stories look far away?",
            "Space stories often use very big backgrounds like planets, craters, and stars. When something small gets close to your face or window, it can look huge against that far background."
        ),
    ],
    "window": [
        (
            "Why should you look again through a window if something seems strange?",
            "A smudge or little thing on the window can trick your eyes. Looking again from a different angle helps you see what is really far away and what is right in front of you."
        ),
    ],
    "visor": [
        (
            "What is a visor?",
            "A visor is the clear front part of a helmet that lets you see out. If something lands on it, your view can get mixed up."
        ),
    ],
    "dome": [
        (
            "What is a clear dome?",
            "A clear dome is a round see-through cover. It lets people look out, but a tiny thing on the dome can look much bigger than it really is."
        ),
    ],
    "robot": [
        (
            "What is a repair robot?",
            "A repair robot is a little machine that helps fix things. In a funny story, even a tiny robot can seem enormous if it is very close to your eyes."
        ),
    ],
    "look_closer": [
        (
            "What should you do before deciding something is scary?",
            "Stop, breathe, and look again. A closer look or a new angle can change what you think you saw."
        ),
    ],
    "wipe": [
        (
            "Why does wiping a clear surface help?",
            "Wiping removes smudges and tiny things that are stuck right in front of your eyes. Then the real view behind them is easier to understand."
        ),
    ],
    "angle": [
        (
            "Why can moving sideways help you see better?",
            "Moving sideways changes your angle, so near things and far things stop lining up the same way. That can make a tricky picture easier to understand."
        ),
    ],
}
KNOWLEDGE_ORDER = ["perspective", "space", "visor", "window", "dome", "robot", "look_closer", "wipe", "angle"]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    mission = world.facts["mission"]
    funny = world.facts["funny"]
    outcome = world.facts["outcome"]
    mood = "with a foamy false alarm and a laugh at the end" if outcome == "foamy_laugh" else "with a calm second look and a laugh at the end"
    return [
        f'Write a funny space adventure for a 3-to-5-year-old that uses the word "perspective".',
        f"Tell a child-friendly mission story where a captain thinks {funny.phrase} is a giant alien because of perspective in {setting.place}, {mood}.",
        f"Write a short space story about {mission.title} where a mistaken view changes after the characters look again from a smarter angle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    captain = world.facts["captain"]
    copilot = world.facts["copilot"]
    setting = world.facts["setting"]
    mission = world.facts["mission"]
    funny = world.facts["funny"]
    fix = world.facts["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Captain {captain.id} and Copilot {copilot.id} on a pretend space mission. They were trying to {mission.goal}."
        ),
        (
            "What problem did Captain see?",
            f"Captain {captain.id} thought a giant alien was blocking {setting.path}. From that perspective, {funny.phrase} looked huge against {setting.backdrop}."
        ),
        (
            "Why did the tiny thing seem so big?",
            f"It was very close to the {setting.surface}, but the background was far away. That perspective trick made the tiny thing cover a big part of the view, so it looked giant."
        ),
    ]
    if world.facts["foam"]:
        qa.append(
            (
                "What happened when Captain got scared?",
                f"Captain {captain.id} pressed the silly alarm button, and joke-foam puffed into the ship. That happened because {captain.pronoun()} reacted before checking the perspective again."
            )
        )
    else:
        qa.append(
            (
                "How did Captain handle the scary moment?",
                f"Captain {captain.id} stopped and listened to {copilot.id}. That helped {captain.pronoun('object')} test the perspective instead of panicking."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They {fix.qa_text}. Then they could see it was only {funny.tiny_truth}.",
        )
    )
    qa.append(
        (
            "What changed by the end?",
            f"At the end, the giant alien was gone because it had never been giant at all. Captain {captain.id} understood the perspective trick and could laugh and finish the mission."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"perspective", "space", "look_closer"}
    setting = world.facts["setting"]
    funny = world.facts["funny"]
    fix = world.facts["fix"]
    tags |= set(setting.tags)
    tags |= set(funny.tags)
    tags |= set(fix.tags)
    if setting.surface == "visor":
        tags.add("visor")
    if setting.surface == "window":
        tags.add("window")
    if setting.surface == "dome":
        tags.add("dome")
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
        if ent.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonwalk",
        mission="cookie",
        object="sticker_star",
        fix="wipe",
        captain="Nova",
        captain_gender="girl",
        copilot="Jett",
        copilot_gender="boy",
        parent="mother",
        trait="jumpy",
        seed=None,
    ),
    StoryParams(
        setting="cockpit",
        mission="flag",
        object="snail_blob",
        fix="step_sideways",
        captain="Milo",
        captain_gender="boy",
        copilot="Luna",
        copilot_gender="girl",
        parent="father",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="station",
        mission="rescue",
        object="wobble_bot",
        fix="step_sideways",
        captain="Ayla",
        captain_gender="girl",
        copilot="Finn",
        copilot_gender="boy",
        parent="mother",
        trait="dramatic",
        seed=None,
    ),
    StoryParams(
        setting="moonwalk",
        mission="flag",
        object="wobble_bot",
        fix="lower_visor",
        captain="Theo",
        captain_gender="boy",
        copilot="Mira",
        copilot_gender="girl",
        parent="father",
        trait="brave",
        seed=None,
    ),
]


def explain_rejection(setting_id: str, object_id: str, fix_id: str) -> str:
    parts = []
    if setting_id in SETTINGS and object_id in OBJECTS:
        setting = SETTINGS[setting_id]
        funny = OBJECTS[object_id]
        if setting.surface not in funny.surfaces:
            parts.append(
                f"{funny.label} cannot plausibly cling to a {setting.surface}, so the perspective mix-up would not start"
            )
    if setting_id in SETTINGS and fix_id in FIXES:
        setting = SETTINGS[setting_id]
        fix = FIXES[fix_id]
        if setting.surface not in fix.surfaces:
            parts.append(
                f"{fix.id} does not work on a {setting.surface}"
            )
    if fix_id in FIXES and FIXES[fix_id].sense < SENSE_MIN:
        parts.append(
            f"'{fix_id}' is known to the world but refused because it is a silly fix instead of a sensible second look"
        )
    if not parts:
        return "(No story: this combination does not fit the world model.)"
    return "(No story: " + "; ".join(parts) + ".)"


ASP_RULES = r"""
valid(S, M, O, F) :- setting(S), mission(M), object(O), fix(F),
                     surface_of(S, Surf), lands_on(O, Surf),
                     works_on(F, Surf), sense(F, Sc), sense_min(Min), Sc >= Min.

panic :- chosen_trait(T), jittery(T).
outcome(foamy_laugh) :- panic.
outcome(calm_laugh) :- not panic.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("surface_of", setting_id, setting.surface))
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for object_id, funny in OBJECTS.items():
        lines.append(asp.fact("object", object_id))
        for surface in sorted(funny.surfaces):
            lines.append(asp.fact("lands_on", object_id, surface))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for surface in sorted(fix.surfaces):
            lines.append(asp.fact("works_on", fix_id, surface))
    for trait in sorted(JITTERY_TRAITS):
        lines.append(asp.fact("jittery", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny space adventure about perspective."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.object and args.fix:
        if not valid_combo(args.setting, args.object, args.fix):
            raise StoryError(explain_rejection(args.setting, args.object, args.fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.setting or next(iter(SETTINGS)), args.object or next(iter(OBJECTS)), args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mission is None or combo[1] == args.mission)
        and (args.object is None or combo[2] == args.object)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        chosen_setting = args.setting or next(iter(SETTINGS))
        chosen_object = args.object or next(iter(OBJECTS))
        chosen_fix = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(chosen_setting, chosen_object, chosen_fix))

    setting_id, mission_id, object_id, fix_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    copilot_gender = "boy" if captain_gender == "girl" else "girl"
    captain = pick_name(rng, captain_gender)
    copilot = pick_name(rng, copilot_gender, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        mission=mission_id,
        object=object_id,
        fix=fix_id,
        captain=captain,
        captain_gender=captain_gender,
        copilot=copilot,
        copilot_gender=copilot_gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.object not in OBJECTS:
        raise StoryError(f"(Unknown object: {params.object})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.fix in FIXES and FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.setting, params.object, params.fix))
    if not valid_combo(params.setting, params.object, params.fix):
        raise StoryError(explain_rejection(params.setting, params.object, params.fix))

    world = tell(
        setting=SETTINGS[params.setting],
        mission=MISSIONS[params.mission],
        funny=OBJECTS[params.object],
        fix=FIXES[params.fix],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        copilot_name=params.copilot,
        copilot_gender=params.copilot_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mission, object, fix) combos:\n")
        for setting_id, mission_id, object_id, fix_id in combos:
            print(f"  {setting_id:8} {mission_id:7} {object_id:12} {fix_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.copilot}: {p.setting}, {p.mission}, {p.object}, {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
