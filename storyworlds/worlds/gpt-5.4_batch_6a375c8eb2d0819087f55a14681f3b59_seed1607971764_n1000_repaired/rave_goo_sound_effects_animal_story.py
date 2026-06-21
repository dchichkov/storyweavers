#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py
=================================================================

A standalone storyworld for a tiny animal-story domain: two young animals make a
moonlit "forest rave" with safe glow-lights and drums, but one child is tempted
to use slippery berry goo as a shortcut to make decorations shine. The goo can
gum up the sound-maker, make the dance patch slippery, and threaten the party.
A calm helper solves the problem with a sensible clean-up tool, and the ending
image proves the animals learned a better way to make a bright, happy show.

The prose is state-driven: the setup establishes a small celebration, the middle
turn grows from the goo getting where it should not, and the ending depends on
whether the chosen fix really handles the mess in time.

Run it
------
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py --animal bunny --goo jam --sound drum
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py --surface stone
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rave_goo_sound_effects_animal_story.py --json
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
    sticky: bool = False
    slippery: bool = False
    noisy: bool = False
    glowing: bool = False
    clean_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class AnimalKind:
    id: str
    label: str
    child_word: str
    move: str
    cheer: str
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
class GooKind:
    id: str
    label: str
    phrase: str
    color: str
    plop: str
    slick_word: str
    sticky: bool = True
    slippery: bool = True
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
class SoundMaker:
    id: str
    label: str
    phrase: str
    beat: str
    sound_word: str
    noisy: bool = True
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
class DanceSurface:
    id: str
    label: str
    phrase: str
    catches_goo: bool
    slippery_when_goo: bool
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
class HelperTool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    clean_text: str
    fail_text: str
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
        return [e for e in self.entities.values() if e.role in {"dreamer", "friend"}]

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


def _r_stick_sound(world: World) -> list[str]:
    out: list[str] = []
    goo = world.get("goo")
    sound = world.get("sound")
    if goo.meters["spilled"] >= THRESHOLD and sound.meters["splashed"] >= THRESHOLD:
        sig = ("stick_sound", sound.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sound.meters["muffled"] += 1
            sound.meters["messy"] += 1
            world.get("party").meters["music_trouble"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__muffle__")
    return out


def _r_slip_patch(world: World) -> list[str]:
    out: list[str] = []
    goo = world.get("goo")
    floor = world.get("floor")
    if goo.meters["spilled"] >= THRESHOLD and floor.attrs.get("slippery_when_goo"):
        sig = ("slip_patch", floor.id)
        if sig not in world.fired:
            world.fired.add(sig)
            floor.meters["slippery"] += 1
            world.get("party").meters["danger"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__slippery__")
    return out


CAUSAL_RULES = [
    Rule(name="stick_sound", tag="physical", apply=_r_stick_sound),
    Rule(name="slip_patch", tag="physical", apply=_r_slip_patch),
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


def hazard_at_risk(goo: GooKind, sound: SoundMaker, surface: DanceSurface) -> bool:
    return goo.sticky and sound.noisy and surface.catches_goo


def sensible_tools() -> list[HelperTool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def mess_severity(sound: SoundMaker, surface: DanceSurface, delay: int) -> int:
    base = 0
    if sound.noisy:
        base += 1
    if surface.slippery_when_goo:
        base += 1
    return base + delay


def is_fixed(tool: HelperTool, sound: SoundMaker, surface: DanceSurface, delay: int) -> bool:
    return tool.power >= mess_severity(sound, surface, delay)


def predict_mess(world: World) -> dict:
    sim = world.copy()
    make_spill(sim, narrate=False)
    return {
        "music_trouble": sim.get("party").meters["music_trouble"],
        "danger": sim.get("party").meters["danger"],
        "muffled": sim.get("sound").meters["muffled"] >= THRESHOLD,
        "slippery": sim.get("floor").meters["slippery"] >= THRESHOLD,
    }


def introduce(world: World, dreamer: Entity, friend: Entity, animal: AnimalKind) -> None:
    dreamer.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In a moonlit clearing, {dreamer.id} and {friend.id} were two little "
        f"{animal.child_word}s getting ready for a forest rave. They tied glow-seed "
        f"lanterns in the branches and giggled because even the leaves seemed ready to dance."
    )


def setup_music(world: World, dreamer: Entity, friend: Entity, sound: SoundMaker) -> None:
    world.say(
        f'{dreamer.id} tapped {sound.phrase}: "{sound.sound_word}! {sound.sound_word}!" '
        f'{friend.id} clapped along, and soon the clearing felt full of beat and bounce.'
    )
    world.say(
        f'"When the music starts, everyone will {friend.attrs.get("move_word", "dance")}!" '
        f"{friend.id} cheered."
    )


def admire_dark_spot(world: World, dreamer: Entity, goo: GooKind, surface: DanceSurface) -> None:
    dreamer.memes["wish"] += 1
    world.say(
        f"Near the middle of the dance patch, {surface.phrase} looked a little plain. "
        f"{dreamer.id} wanted it to shine brighter than the lanterns."
    )
    world.say(
        f'{dreamer.id} spotted {goo.phrase} by the snack stump and whispered, '
        f'"This {goo.label} is shiny. Maybe a little dab would make the whole floor sparkle."'
    )


def warn(world: World, friend: Entity, dreamer: Entity, goo: GooKind, sound: SoundMaker,
         surface: DanceSurface) -> None:
    pred = predict_mess(world)
    friend.memes["care"] += 1
    world.facts["predicted_music_trouble"] = pred["music_trouble"]
    world.facts["predicted_danger"] = pred["danger"]
    extra = []
    if pred["muffled"]:
        extra.append(f"gum up the {sound.label}")
    if pred["slippery"]:
        extra.append(f"make {surface.label} too slick")
    risk = " and ".join(extra) if extra else "make a mess"
    world.say(
        f'{friend.id} twitched {friend.pronoun("possessive")} nose. '
        f'"Please don\'t smear the {goo.label} there. It could {risk}, and then the party would not feel fun at all."'
    )


def defy(world: World, dreamer: Entity, goo: GooKind) -> None:
    dreamer.memes["defiance"] += 1
    world.say(
        f'{dreamer.id} gave a hopeful little grin. "Just one tiny splash," '
        f'{dreamer.pronoun()} said.'
    )
    world.say(f"Plip! {dreamer.id} tipped the {goo.label} anyway.")


def make_spill(world: World, narrate: bool = True) -> None:
    goo = world.get("goo")
    sound = world.get("sound")
    floor = world.get("floor")
    goo.meters["spilled"] += 1
    sound.meters["splashed"] += 1
    floor.meters["goo_on_floor"] += 1
    propagate(world, narrate=narrate)


def spill_scene(world: World, goo: GooKind, sound: SoundMaker, surface: DanceSurface) -> None:
    make_spill(world, narrate=False)
    world.say(
        f"{goo.plop} went the {goo.color} {goo.label} as it splashed across {surface.phrase}. "
        f"Some of it slid onto the {sound.label}, and at once the happy beat turned into "
        f'"{sound.sound_word}... glorp... {sound.sound_word}?"'
    )
    if world.get("floor").meters["slippery"] >= THRESHOLD:
        world.say(
            f"The middle of the dance patch turned {goo.slick_word}, and everyone took tiny careful steps."
        )


def alarm(world: World, friend: Entity, helper: Entity) -> None:
    world.say(f'"Oh no! The music is sticky!" cried {friend.id}.')
    world.say(f'"{helper.id.upper()}!"')


def helper_arrives(world: World, helper: Entity, tool: HelperTool, sound: SoundMaker,
                   surface: DanceSurface) -> None:
    sound.meters["muffled"] = 0.0
    sound.meters["messy"] = 0.0
    world.get("floor").meters["slippery"] = 0.0
    world.get("party").meters["music_trouble"] = 0.0
    world.get("party").meters["danger"] = 0.0
    world.say(
        f"{helper.id} hurried over. {helper.pronoun().capitalize()} {tool.clean_text.format(sound=sound.label, surface=surface.label)}."
    )
    world.say(
        f'Soon the beat came back: "{sound.sound_word}! {sound.sound_word}!" and the dance patch felt safe again.'
    )


def helper_fails(world: World, helper: Entity, tool: HelperTool, sound: SoundMaker,
                 surface: DanceSurface) -> None:
    world.get("party").meters["danger"] += 1
    world.get("party").meters["music_trouble"] += 1
    world.say(
        f"{helper.id} tried, but {helper.pronoun()} {tool.fail_text.format(sound=sound.label, surface=surface.label)}."
    )
    world.say(
        f'The beat stayed wrong -- "{sound.sound_word}... glorp..." -- and no one wanted to leap on {surface.phrase}.'
    )


def lesson(world: World, helper: Entity, dreamer: Entity, friend: Entity, goo: GooKind,
           animal: AnimalKind) -> None:
    dreamer.memes["lesson"] += 1
    friend.memes["relief"] += 1
    dreamer.memes["relief"] += 1
    world.say(
        f'{helper.id} knelt beside the little {animal.child_word}s. '
        f'"Shiny is lovely," {helper.pronoun()} said, "but {goo.label} belongs on snacks, not on dance floors or music tools."'
    )
    world.say(
        f'{dreamer.id} lowered {dreamer.pronoun("possessive")} ears. '
        f'"I wanted the rave to look extra bright," {dreamer.pronoun()} murmured. '
        f'"Next time I will ask before I splash."'
    )


def sad_lesson(world: World, helper: Entity, dreamer: Entity, friend: Entity, goo: GooKind) -> None:
    dreamer.memes["lesson"] += 1
    friend.memes["relief"] += 1
    dreamer.memes["sadness"] += 1
    world.say(
        f'{helper.id} wrapped both children in a gentle hug. '
        f'"The good part is that everyone is safe," {helper.pronoun()} said. '
        f'"But goo does not belong where feet can slip and music can stick."'
    )
    world.say(
        f"{dreamer.id} and {friend.id} helped carry the sticky things away, and the party had to end early."
    )


def safer_alternative(world: World, helper: Entity, dreamer: Entity, friend: Entity,
                      animal: AnimalKind, sound: SoundMaker) -> None:
    dreamer.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"The next evening, {helper.id} brought a basket of glow petals that shone without any mess at all."
    )
    world.say(
        f"{dreamer.id} scattered them around the clearing, {friend.id} tapped the {sound.label}, "
        f'and the music sang "{sound.sound_word}! {sound.sound_word}!" brighter than ever.'
    )
    world.say(
        f"Under the silver moon, the little {animal.child_word}s twirled and {animal.move}d through their rave -- bright, bouncy, and clean."
    )


def quiet_end(world: World, dreamer: Entity, friend: Entity, animal: AnimalKind) -> None:
    world.say(
        f"That night the clearing grew quiet. {dreamer.id} and {friend.id} sat close together and listened to crickets instead."
    )
    world.say(
        f"They still dreamed of a grand rave, but now they knew that fun must stay safe for little {animal.child_word}s."
    )


def tell(animal: AnimalKind, goo: GooKind, sound: SoundMaker, surface: DanceSurface,
         tool: HelperTool, dreamer_name: str = "Pip", friend_name: str = "Moss",
         helper_name: str = "Aunt Fern", delay: int = 0) -> World:
    world = World()
    dreamer = world.add(Entity(id=dreamer_name, kind="character", type=animal.id, role="dreamer"))
    friend = world.add(Entity(id=friend_name, kind="character", type=animal.id, role="friend",
                              attrs={"move_word": animal.move}))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult_animal", role="helper"))
    party = world.add(Entity(id="party", type="party", label="the party"))
    floor = world.add(Entity(id="floor", type="surface", label=surface.label,
                             attrs={"slippery_when_goo": surface.slippery_when_goo}))
    goo_ent = world.add(Entity(id="goo", type="goo", label=goo.label,
                               sticky=goo.sticky, slippery=goo.slippery))
    sound_ent = world.add(Entity(id="sound", type="sound", label=sound.label, noisy=sound.noisy))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, clean_tool=True))

    world.facts.update(
        animal=animal,
        goo_cfg=goo,
        sound_cfg=sound,
        surface_cfg=surface,
        tool_cfg=tool,
        dreamer=dreamer,
        friend=friend,
        helper=helper,
        party=party,
        floor=floor,
        goo=goo_ent,
        sound=sound_ent,
        tool=tool_ent,
        delay=delay,
    )

    introduce(world, dreamer, friend, animal)
    setup_music(world, dreamer, friend, sound)
    world.para()
    admire_dark_spot(world, dreamer, goo, surface)
    warn(world, friend, dreamer, goo, sound, surface)
    defy(world, dreamer, goo)
    world.para()
    spill_scene(world, goo, sound, surface)
    alarm(world, friend, helper)
    world.para()

    fixed = is_fixed(tool, sound, surface, delay)
    if fixed:
        helper_arrives(world, helper, tool, sound, surface)
        lesson(world, helper, dreamer, friend, goo, animal)
        world.para()
        safer_alternative(world, helper, dreamer, friend, animal, sound)
        outcome = "restored"
    else:
        helper_fails(world, helper, tool, sound, surface)
        sad_lesson(world, helper, dreamer, friend, goo)
        world.para()
        quiet_end(world, dreamer, friend, animal)
        outcome = "ended_early"

    world.facts.update(
        outcome=outcome,
        spilled=world.get("goo").meters["spilled"] >= THRESHOLD,
        muffled_before_fix=sound_ent.meters["splashed"] >= THRESHOLD,
        slippery_before_fix=surface.slippery_when_goo,
        fixed=fixed,
        severity=mess_severity(sound, surface, delay),
    )
    return world


ANIMALS = {
    "bunny": AnimalKind(
        id="bunny",
        label="bunny",
        child_word="bunny",
        move="hop",
        cheer="thump-thump",
        tags={"rave", "animal"},
    ),
    "fox": AnimalKind(
        id="fox",
        label="fox",
        child_word="fox",
        move="skip",
        cheer="swish-swish",
        tags={"rave", "animal"},
    ),
    "otter": AnimalKind(
        id="otter",
        label="otter",
        child_word="otter",
        move="spin",
        cheer="splash-splash",
        tags={"rave", "animal"},
    ),
}

GOOS = {
    "jam": GooKind(
        id="jam",
        label="berry jam goo",
        phrase="a bowl of berry jam goo",
        color="purple",
        plop="Splat",
        slick_word="slick and sticky",
        tags={"goo", "sticky"},
    ),
    "sap": GooKind(
        id="sap",
        label="tree sap goo",
        phrase="a cup of tree sap goo",
        color="golden",
        plop="Glorp",
        slick_word="slimy and shiny",
        tags={"goo", "sticky"},
    ),
    "mash": GooKind(
        id="mash",
        label="plum mash goo",
        phrase="a pot of plum mash goo",
        color="violet",
        plop="Splish",
        slick_word="squishy and slick",
        tags={"goo", "sticky"},
    ),
}

SOUNDS = {
    "drum": SoundMaker(
        id="drum",
        label="moss drum",
        phrase="the moss drum",
        beat="beat",
        sound_word="boom-boom",
        tags={"drum", "sound_effects"},
    ),
    "tambourine": SoundMaker(
        id="tambourine",
        label="seed-pod tambourine",
        phrase="the seed-pod tambourine",
        beat="jingle",
        sound_word="jingle-jingle",
        tags={"tambourine", "sound_effects"},
    ),
    "rattle": SoundMaker(
        id="rattle",
        label="acorn rattle",
        phrase="the acorn rattle",
        beat="shake",
        sound_word="shake-shake",
        tags={"rattle", "sound_effects"},
    ),
}

SURFACES = {
    "moss": DanceSurface(
        id="moss",
        label="the mossy dance patch",
        phrase="the mossy dance patch",
        catches_goo=True,
        slippery_when_goo=True,
        tags={"moss"},
    ),
    "roots": DanceSurface(
        id="roots",
        label="the flat roots",
        phrase="the flat roots by the oak tree",
        catches_goo=True,
        slippery_when_goo=True,
        tags={"roots"},
    ),
    "stone": DanceSurface(
        id="stone",
        label="the stone ring",
        phrase="the stone ring in the clearing",
        catches_goo=False,
        slippery_when_goo=False,
        tags={"stone"},
    ),
}

TOOLS = {
    "warm_water": HelperTool(
        id="warm_water",
        label="warm water and cloth",
        phrase="a warm bowl and cloth",
        sense=3,
        power=3,
        clean_text="used warm water and a soft cloth to wipe the {sound} clean and scrub the goo from {surface}",
        fail_text="dabbed at the sticky mess, but the goo stayed smeared across the {sound} and {surface}",
        qa_text="used warm water and a cloth to wash the goo away",
        tags={"cleaning", "warm_water"},
    ),
    "sand_cover": HelperTool(
        id="sand_cover",
        label="dry sand scoop",
        phrase="a scoop of dry sand",
        sense=2,
        power=2,
        clean_text="sprinkled dry sand over the slick spots, swept the goo away, and rubbed the {sound} until it could sing again",
        fail_text="sprinkled a little dry sand, but the goo still clung to the {sound} and left {surface} too messy",
        qa_text="used dry sand and sweeping to soak up the goo",
        tags={"cleaning", "sand"},
    ),
    "leaf_fan": HelperTool(
        id="leaf_fan",
        label="leaf fan",
        phrase="a broad leaf fan",
        sense=1,
        power=1,
        clean_text="fanned the mess hopefully and puffed little breezes over the {sound}",
        fail_text="only blew the smell around, while the goo kept sticking to the {sound} and slicking {surface}",
        qa_text="tried to fan the goo away",
        tags={"fan"},
    ),
}

GIRLISH_NAMES = ["Pip", "Mimi", "Lulu", "Nori", "Tansy", "Poppy"]
NEUTRAL_NAMES = ["Moss", "Pebble", "Clover", "Juniper", "Sunny", "Bramble"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for animal_id in ANIMALS:
        for goo_id, goo in GOOS.items():
            for sound_id, sound in SOUNDS.items():
                for surface_id, surface in SURFACES.items():
                    if hazard_at_risk(goo, sound, surface):
                        combos.append((animal_id, goo_id, sound_id, surface_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    goo: str
    sound: str
    surface: str
    tool: str
    dreamer_name: str
    friend_name: str
    helper_name: str
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


KNOWLEDGE = {
    "goo": [
        ("What is goo?",
         "Goo is a sticky, squishy mess. It can be fun in the right place, but it can also make tools sticky and floors slippery.")
    ],
    "rave": [
        ("What is a rave in this story?",
         "Here it means a lively little dance party with music and lights. It is a playful animal celebration, not something scary.")
    ],
    "drum": [
        ("What does a drum sound like?",
         'A drum makes a beat when you tap it, often something like "boom-boom." The beat helps dancers move together.')
    ],
    "tambourine": [
        ("What sound does a tambourine make?",
         'A tambourine can jingle when it shakes. Its tiny parts rattle together to make bright sounds.')
    ],
    "rattle": [
        ("What is a rattle?",
         "A rattle is something you shake to make sound. Little pieces inside bump together and make a rhythm.")
    ],
    "cleaning": [
        ("Why should sticky goo be cleaned up quickly?",
         "Sticky goo can cling to tools and make them stop working well. It can also leave a patch that makes feet slip.")
    ],
    "warm_water": [
        ("Why does warm water help with sticky messes?",
         "Warm water can loosen a sticky mess so it wipes away more easily. That makes cleaning gentler and faster.")
    ],
    "sand": [
        ("How can dry sand help with a spill?",
         "Dry sand can soak up some wet stickiness so it is easier to sweep away. It helps best when someone also cleans carefully.")
    ],
}
KNOWLEDGE_ORDER = ["rave", "goo", "drum", "tambourine", "rattle", "cleaning", "warm_water", "sand"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    goo = f["goo_cfg"]
    sound = f["sound_cfg"]
    outcome = f["outcome"]
    if outcome == "ended_early":
        return [
            f'Write an animal story for a 3-to-5-year-old that includes the words "rave" and "goo" and uses sound effects like "{sound.sound_word}".',
            f"Tell a gentle cautionary tale where two little {animal.child_word}s prepare a moonlit rave, but sticky {goo.label} ruins the music and the party ends early.",
            f"Write a story about a child who wants something shiny right away, makes a sticky mess, and learns that bright ideas should also be safe ideas.",
        ]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "rave" and "goo" and uses sound effects like "{sound.sound_word}".',
        f"Tell a warm story where two little {animal.child_word}s start a forest rave, a sticky goo causes trouble, and a calm helper fixes it.",
        f"Write a simple animal story with a messy middle, a safe clean-up, and an ending where music comes back brighter than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dreamer = f["dreamer"]
    friend = f["friend"]
    helper = f["helper"]
    animal = f["animal"]
    goo = f["goo_cfg"]
    sound = f["sound_cfg"]
    surface = f["surface_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]

    qa = [
        (
            "Who is the story about?",
            f"It is about two little {animal.child_word}s named {dreamer.id} and {friend.id}, and {helper.id} who comes to help them. They are getting ready for a moonlit rave in the clearing."
        ),
        (
            "What were they getting ready for?",
            f"They were getting ready for a forest rave with glow-lights and music. The happy beat from the {sound.label} made the clearing feel like a tiny dance party."
        ),
        (
            f"Why did {friend.id} warn {dreamer.id} about the goo?",
            f"{friend.id} warned that the {goo.label} could gum up the {sound.label} and make {surface.label} too slick. That would spoil the music and make dancing unsafe."
        ),
        (
            f"What happened when {dreamer.id} tipped the goo?",
            f"The {goo.label} splashed across the dance patch and onto the {sound.label}. The beat changed from a happy rhythm into a sticky, silly noise because the instrument got messy."
        ),
    ]
    if outcome == "restored":
        qa.extend([
            (
                f"How did {helper.id} solve the problem?",
                f"{helper.id} {tool.qa_text}. That cleaned the instrument and the floor, so the music and dancing could start again."
            ),
            (
                "How did the story end?",
                f"The next evening they used glow petals instead of goo, and the rave felt bright, bouncy, and clean. The ending shows they found a safer way to make the party beautiful."
            ),
            (
                f"What did {dreamer.id} learn?",
                f"{dreamer.id} learned that shiny shortcuts are not always wise. Before using a messy thing, {dreamer.pronoun()} should ask and think about what it might do next."
            ),
        ])
    else:
        qa.extend([
            (
                f"Could {helper.id} fix the mess in time?",
                f"No. {helper.id} tried, but the sticky mess stayed on the {sound.label} and the dance patch still felt wrong. Because the problem was not really fixed, the party had to end early."
            ),
            (
                "How did the story end?",
                f"The clearing grew quiet, and the little {animal.child_word}s listened to crickets instead of dancing. The calm ending shows they stayed safe, even though the party was over."
            ),
            (
                f"What did {dreamer.id} and {friend.id} learn?",
                f"They learned that goo does not belong on floors or music tools. A fun idea must also be a safe idea if everyone wants to keep dancing."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["goo_cfg"].tags) | set(f["sound_cfg"].tags) | set(f["tool_cfg"].tags) | {"rave"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (
            ("sticky", e.sticky),
            ("slippery", e.slippery),
            ("noisy", e.noisy),
            ("glowing", e.glowing),
            ("clean_tool", e.clean_tool),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="bunny",
        goo="jam",
        sound="drum",
        surface="moss",
        tool="warm_water",
        dreamer_name="Pip",
        friend_name="Moss",
        helper_name="Aunt Fern",
        delay=0,
    ),
    StoryParams(
        animal="fox",
        goo="sap",
        sound="tambourine",
        surface="roots",
        tool="sand_cover",
        dreamer_name="Juniper",
        friend_name="Pebble",
        helper_name="Uncle Reed",
        delay=0,
    ),
    StoryParams(
        animal="otter",
        goo="mash",
        sound="rattle",
        surface="moss",
        tool="leaf_fan",
        dreamer_name="Sunny",
        friend_name="Bramble",
        helper_name="Aunt Willow",
        delay=1,
    ),
]


def explain_rejection(goo: GooKind, sound: SoundMaker, surface: DanceSurface) -> str:
    if not surface.catches_goo:
        return (
            f"(No story: {surface.phrase} would not really hold the {goo.label}, so the goo would not make a convincing sticky dance-patch problem. "
            f"Pick a softer surface like moss or roots.)"
        )
    if not goo.sticky:
        return f"(No story: {goo.label} is not sticky enough to gum up the {sound.label}.)"
    return "(No story: this combination does not create a believable goo-and-music problem.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = " / ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.tool not in TOOLS:
        return "?"
    return "restored" if is_fixed(TOOLS[params.tool], SOUNDS[params.sound], SURFACES[params.surface], params.delay) else "ended_early"


ASP_RULES = r"""
hazard(G,Su,So) :- goo(G), sound(Su), surface(So), sticky(G), noisy(Su), catches_goo(So).
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

base_severity(Su,So,2) :- noisy(Su), slippery_when_goo(So).
base_severity(Su,So,1) :- noisy(Su), not slippery_when_goo(So).
severity(V) :- chosen_sound(Su), chosen_surface(So), delay(D), base_severity(Su,So,B), V = B + D.

restored :- chosen_tool(T), power(T,P), severity(V), P >= V.
outcome(restored) :- restored.
outcome(ended_early) :- not restored.

valid(A,G,Su,So) :- animal(A), hazard(G,Su,So).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for gid, goo in GOOS.items():
        lines.append(asp.fact("goo", gid))
        if goo.sticky:
            lines.append(asp.fact("sticky", gid))
        if goo.slippery:
            lines.append(asp.fact("slippery", gid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if sound.noisy:
            lines.append(asp.fact("noisy", sid))
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        if surface.catches_goo:
            lines.append(asp.fact("catches_goo", sid))
        if surface.slippery_when_goo:
            lines.append(asp.fact("slippery_when_goo", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("power", tid, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_sound", params.sound),
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_tools = set(asp_sensible_tools())
    p_tools = {t.id for t in sensible_tools()}
    if c_tools == p_tools:
        print(f"OK: sensible tools match ({sorted(c_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_tools)} python={sorted(p_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a moonlit rave, sticky goo, sound effects, and a safer way to shine."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--goo", choices=GOOS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before the helper acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and not SURFACES[args.surface].catches_goo:
        goo = GOOS[args.goo] if args.goo else next(iter(GOOS.values()))
        sound = SOUNDS[args.sound] if args.sound else next(iter(SOUNDS.values()))
        raise StoryError(explain_rejection(goo, sound, SURFACES[args.surface]))
    if args.goo and args.sound and args.surface:
        goo = GOOS[args.goo]
        sound = SOUNDS[args.sound]
        surface = SURFACES[args.surface]
        if not hazard_at_risk(goo, sound, surface):
            raise StoryError(explain_rejection(goo, sound, surface))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        c for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.goo is None or c[1] == args.goo)
        and (args.sound is None or c[2] == args.sound)
        and (args.surface is None or c[3] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, goo, sound, surface = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(t.id for t in sensible_tools()))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    names = rng.sample(NEUTRAL_NAMES + GIRLISH_NAMES, 3)
    dreamer_name = names[0]
    friend_name = names[1]
    helper_name = "Aunt Fern" if rng.choice([True, False]) else "Uncle Reed"

    return StoryParams(
        animal=animal,
        goo=goo,
        sound=sound,
        surface=surface,
        tool=tool,
        dreamer_name=dreamer_name,
        friend_name=friend_name,
        helper_name=helper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.goo not in GOOS:
        raise StoryError(f"(Unknown goo: {params.goo})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not hazard_at_risk(GOOS[params.goo], SOUNDS[params.sound], SURFACES[params.surface]):
        raise StoryError(explain_rejection(GOOS[params.goo], SOUNDS[params.sound], SURFACES[params.surface]))
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))

    world = tell(
        animal=ANIMALS[params.animal],
        goo=GOOS[params.goo],
        sound=SOUNDS[params.sound],
        surface=SURFACES[params.surface],
        tool=TOOLS[params.tool],
        dreamer_name=params.dreamer_name,
        friend_name=params.friend_name,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, goo, sound, surface) combos:\n")
        for animal, goo, sound, surface in combos:
            print(f"  {animal:8} {goo:6} {sound:11} {surface}")
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
            header = f"### {p.dreamer_name} & {p.friend_name}: {p.goo} on {p.surface} with {p.sound} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
