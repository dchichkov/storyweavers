#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py
=============================================================================

A standalone story world for a small Animal Story domain built around a sunday
breeze, a chair, and a strange sound.

Premise
-------
A young animal looks forward to resting in a favorite chair on sunday. Then a
breeze makes something nearby go clink-clink, flap-flap, or creak-creak, and
the chair suddenly feels spooky. An older helper investigates, finds the true
cause, fixes it sensibly, and the ending image proves the chair has become cozy
again.

Run it
------
python storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py
python storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py --place porch --chair rocking --source rocker_joint --fix oil_joint
python storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py --source ribbon --fix move_teacup
python storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py --all --qa
python storyworlds/worlds/gpt-5.4/breeze_chair_sunday_sound_effects_animal_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit_girl", "squirrel_girl", "mouse_girl", "hedgehog_girl"}
        male = {"rabbit_boy", "squirrel_boy", "mouse_boy", "hedgehog_boy", "badger_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    chairs: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
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
class ChairKind:
    id: str
    label: str
    phrase: str
    motion: str
    comfy: str
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
class SoundSource:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    reveal: str
    scare: str
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
    label: str
    action: str
    success: str
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
class Animal:
    id: str
    species_word: str
    type: str
    trait: str
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


def _r_breeze_sound(world: World) -> list[str]:
    breeze = world.get("breeze")
    source = world.get("source")
    chair = world.get("chair")
    hero = world.get("hero")
    if breeze.meters["gust"] < THRESHOLD or source.meters["fixed"] >= THRESHOLD:
        return []
    sig = ("breeze_sound", int(breeze.meters["gust"]), source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["rattling"] += 1
    chair.meters["noisy"] += 1
    hero.memes["worry"] += 1
    return ["__sound__"]


def _r_worry_pause(world: World) -> list[str]:
    hero = world.get("hero")
    chair = world.get("chair")
    if hero.memes["worry"] < THRESHOLD:
        return []
    sig = ("worry_pause", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chair.meters["unused"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="breeze_sound", tag="physical", apply=_r_breeze_sound),
    Rule(name="worry_pause", tag="emotional", apply=_r_worry_pause),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def source_fits(place_id: str, chair_id: str, source_id: str) -> bool:
    if chair_id not in CHAIRS:
        return False
    if source_id not in SOURCES:
        return False
    if place_id not in PLACES:
        return False
    place = PLACES[place_id]
    if chair_id not in place.chairs or source_id not in place.sources:
        return False
    if source_id == "rocker_joint":
        return chair_id == "rocking"
    if source_id == "ribbon":
        return chair_id in {"wicker", "folding"}
    return True


def fix_works(source_id: str, fix_id: str) -> bool:
    return fix_id in SOURCE_TO_FIXES.get(source_id, set())


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for chair_id in sorted(place.chairs):
            for source_id in sorted(place.sources):
                if not source_fits(place_id, chair_id, source_id):
                    continue
                for fix_id in sorted(SOURCE_TO_FIXES.get(source_id, set())):
                    combos.append((place_id, chair_id, source_id, fix_id))
    return combos


def explain_rejection(place_id: str, chair_id: str, source_id: str) -> str:
    if place_id in PLACES and chair_id in CHAIRS and chair_id not in PLACES[place_id].chairs:
        return (f"(No story: {PLACES[place_id].label} does not have {CHAIRS[chair_id].phrase}, "
                f"so the chair would not belong in that scene.)")
    if place_id in PLACES and source_id in SOURCES and source_id not in PLACES[place_id].sources:
        return (f"(No story: {SOURCES[source_id].label} does not belong near the chair in "
                f"{PLACES[place_id].label}, so the breeze would have nothing reasonable to shake there.)")
    if source_id == "rocker_joint" and chair_id != "rocking":
        return "(No story: only a rocking chair can make the old joint creak-creak.)"
    if source_id == "ribbon" and chair_id not in {"wicker", "folding"}:
        return "(No story: that ribbon is tied to a light chair, not to a heavy rocking chair.)"
    return "(No story: that place, chair, and sound source do not make a sensible combination.)"


def explain_fix(source_id: str, fix_id: str) -> str:
    if source_id not in SOURCES or fix_id not in FIXES:
        return "(No story: unknown source or fix.)"
    good = ", ".join(sorted(SOURCE_TO_FIXES.get(source_id, set())))
    return (f"(No story: {FIXES[fix_id].label} would not stop {SOURCES[source_id].label}. "
            f"Try one of: {good}.)")


def predict_sound(world: World) -> dict:
    sim = world.copy()
    sim.get("breeze").meters["gust"] += 1
    propagate(sim, narrate=False)
    source = sim.get("source")
    hero = sim.get("hero")
    return {
        "sounds": source.meters["rattling"] >= THRESHOLD,
        "fear": hero.memes["worry"],
        "sound_word": sim.facts.get("sound_word", ""),
    }


def introduce(world: World, hero: Entity, helper: Entity, chair: Entity, chair_cfg: ChairKind) -> None:
    world.say(
        f"On sunday morning, {hero.id} the little {hero.attrs['species_word']} padded to "
        f"{world.place.label}. A mild breeze brushed the leaves, and {helper.id} had set "
        f"out {chair_cfg.phrase} just where the sun felt warm."
    )
    world.say(
        f"{hero.id} loved that chair because it could {chair_cfg.motion}, and because "
        f"{chair_cfg.comfy}."
    )


def settle_in(world: World, hero: Entity) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        f"{hero.id} climbed onto the seat with a berry-book and tucked {hero.pronoun('possessive')} "
        f"paws neatly under {hero.pronoun('object')}."
    )


def breeze_rises(world: World, breeze: Entity, source_cfg: SoundSource) -> None:
    breeze.meters["gust"] += 1
    world.facts["sound_word"] = source_cfg.sound
    propagate(world, narrate=False)
    world.say(
        f"Then the breeze puffed a little harder. {source_cfg.sound.capitalize()}! "
        f"{source_cfg.reveal}."
    )


def startle(world: World, hero: Entity, source_cfg: SoundSource) -> None:
    hero.memes["imagination"] += 1
    world.say(
        f"{hero.id} froze. To {hero.pronoun('object')}, the sound felt like {source_cfg.scare}."
    )
    if "cautious" in hero.traits:
        world.say(
            f"{hero.pronoun().capitalize()} slipped off the chair at once and pressed close to the porch post."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} leaned down for one tiny peek, but the next sound still made "
            f"{hero.pronoun('object')} hop back."
        )


def helper_predicts(world: World, helper: Entity, source_cfg: SoundSource) -> None:
    pred = predict_sound(world)
    helper.memes["attention"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{helper.id} lifted one ear and listened. "That sounds like the breeze touching something," '
        f"{helper.pronoun()} said. {helper.pronoun().capitalize()} glanced around the chair and noticed "
        f"{source_cfg.clue}."
    )


def investigate(world: World, hero: Entity, helper: Entity, source_cfg: SoundSource) -> None:
    hero.memes["courage"] += 1
    if hero.memes["worry"] > hero.memes["courage"]:
        world.say(
            f"{hero.id} stayed one step behind {helper.id}, but {hero.pronoun()} followed anyway."
        )
    else:
        world.say(
            f"{hero.id} took a brave breath and padded beside {helper.id} to look closer."
        )
    world.say(
        f"Together they found the true cause: {source_cfg.phrase}."
    )


def apply_fix(world: World, helper: Entity, source: Entity, fix_cfg: Fix) -> None:
    source.meters["fixed"] = 1.0
    source.meters["rattling"] = 0.0
    world.get("chair").meters["noisy"] = 0.0
    world.get("hero").memes["worry"] = 0.0
    world.get("hero").memes["relief"] += 1
    world.get("hero").memes["joy"] += 1
    world.say(
        f"{helper.id} {fix_cfg.action}. The little sound stopped at once."
    )


def test_again(world: World, breeze: Entity, hero: Entity) -> None:
    breeze.meters["gust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A fresh breeze came through again. This time there was only a soft hush in the grass, "
        f"and no silly clatter near the chair."
    )
    hero.memes["trust"] += 1


def ending(world: World, hero: Entity, helper: Entity, chair_cfg: ChairKind) -> None:
    world.get("chair").meters["occupied"] += 1
    world.say(
        f"{hero.id} climbed back into the chair and gave it one careful little sway. "
        f"When nothing spooky answered, {hero.pronoun()} smiled."
    )
    world.say(
        f"Soon {hero.id} and {helper.id} were sharing crumbs and stories in the sunday breeze, "
        f"while the chair {chair_cfg.motion} as gently as a nest."
    )


def tell(
    place: Place,
    chair_cfg: ChairKind,
    source_cfg: SoundSource,
    fix_cfg: Fix,
    hero_cfg: Animal,
    helper_cfg: Animal,
) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_cfg.id,
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.id,
        role="hero",
        traits=[hero_cfg.trait],
        attrs={"species_word": hero_cfg.species_word},
        tags=set(hero_cfg.tags),
    ))
    helper = world.add(Entity(
        id=helper_cfg.id,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.id,
        role="helper",
        traits=[helper_cfg.trait],
        attrs={"species_word": helper_cfg.species_word},
        tags=set(helper_cfg.tags),
    ))
    chair = world.add(Entity(
        id="chair",
        kind="thing",
        type="chair",
        label=chair_cfg.label,
        role="chair",
        tags=set(chair_cfg.tags),
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        role="source",
        tags=set(source_cfg.tags),
    ))
    breeze = world.add(Entity(
        id="breeze",
        kind="thing",
        type="weather",
        label="breeze",
        role="weather",
        tags={"breeze", "wind"},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        chair_cfg=chair_cfg,
        source_cfg=source_cfg,
        fix_cfg=fix_cfg,
        place_cfg=place,
        sound_word=source_cfg.sound,
        brave_follow=False,
    )

    introduce(world, hero, helper, chair, chair_cfg)
    settle_in(world, hero)

    world.para()
    breeze_rises(world, breeze, source_cfg)
    startle(world, hero, source_cfg)

    world.para()
    helper_predicts(world, helper, source_cfg)
    investigate(world, hero, helper, source_cfg)
    world.facts["brave_follow"] = hero.memes["courage"] >= THRESHOLD
    apply_fix(world, helper, source, fix_cfg)

    world.para()
    test_again(world, breeze, hero)
    ending(world, hero, helper, chair_cfg)

    world.facts["resolved"] = source.meters["fixed"] >= THRESHOLD
    world.facts["chair_used_at_end"] = world.get("chair").meters["occupied"] >= THRESHOLD
    return world


PLACES = {
    "porch": Place(
        id="porch",
        label="the sunny porch",
        scene="a porch with flower boxes and a rail for hanging things",
        chairs={"rocking", "wicker"},
        sources={"rocker_joint", "wind_chime", "teacup"},
        tags={"porch"},
    ),
    "garden": Place(
        id="garden",
        label="the bean garden path",
        scene="a garden path under tall bean vines",
        chairs={"wicker", "folding"},
        sources={"ribbon", "teacup", "wind_chime"},
        tags={"garden"},
    ),
    "apple_tree": Place(
        id="apple_tree",
        label="the apple-tree shade",
        scene="a patch of shade under a wide old apple tree",
        chairs={"wicker", "folding"},
        sources={"ribbon", "wind_chime"},
        tags={"tree"},
    ),
}

CHAIRS = {
    "rocking": ChairKind(
        id="rocking",
        label="rocking chair",
        phrase="a round-backed rocking chair",
        motion="rock",
        comfy="the curved arms felt safe and snug",
        tags={"chair", "rocking_chair"},
    ),
    "wicker": ChairKind(
        id="wicker",
        label="wicker chair",
        phrase="a honey-colored wicker chair",
        motion="creak a tiny bit when someone settled in",
        comfy="the woven seat held a soft striped cushion",
        tags={"chair", "wicker"},
    ),
    "folding": ChairKind(
        id="folding",
        label="folding chair",
        phrase="a painted folding chair",
        motion="tip back just enough for cloud-looking",
        comfy="its patchwork blanket made a warm lap",
        tags={"chair", "folding_chair"},
    ),
}

SOURCES = {
    "rocker_joint": SoundSource(
        id="rocker_joint",
        label="the loose rocker joint",
        phrase="a loose joint under the rocker runner",
        sound="creak-creak",
        clue="a tiny silver screw shining where the wood met the runner",
        reveal="The rocking chair answered with a long creak-creak from below",
        scare="a grumpy old porch goblin clearing its throat",
        tags={"creak", "chair_part"},
    ),
    "wind_chime": SoundSource(
        id="wind_chime",
        label="the shell wind chime",
        phrase="a shell wind chime hanging above the chair",
        sound="clink-clink",
        clue="two little shells tapping each other over the chair arm",
        reveal="The shells over the chair knocked together: clink-clink",
        scare="tiny glass teeth chattering in the air",
        tags={"wind_chime", "clink"},
    ),
    "ribbon": SoundSource(
        id="ribbon",
        label="the loose picnic ribbon",
        phrase="a loose picnic ribbon tied to the chair back",
        sound="flap-flap",
        clue="a red ribbon whisking hard against the slats",
        reveal="A bright ribbon slapped the chair back with a flap-flap",
        scare="small wings from an unseen bird",
        tags={"ribbon", "flap"},
    ),
    "teacup": SoundSource(
        id="teacup",
        label="the spoon in the teacup",
        phrase="a spoon rattling inside a tiny teacup on the chair arm",
        sound="ting-ting",
        clue="the spoon bumping the cup each time the chair twitched",
        reveal="The spoon in a little teacup rang out: ting-ting",
        scare="a secret bell asking who was there",
        tags={"teacup", "clink"},
    ),
}

FIXES = {
    "oil_joint": Fix(
        id="oil_joint",
        label="a drop of walnut oil",
        action="rubbed a drop of walnut oil into the loose joint and pressed the wood snug again",
        success="The joint stopped rubbing and the creak went away.",
        qa_text="rubbed walnut oil into the loose joint and pressed it snug",
        tags={"repair", "oil"},
    ),
    "hang_chime": Fix(
        id="hang_chime",
        label="a higher hook",
        action="lifted the shell wind chime onto a higher hook where it could swing free",
        success="The shells no longer knocked against each other over the chair.",
        qa_text="moved the shell wind chime to a higher hook",
        tags={"repair", "wind_chime"},
    ),
    "tie_ribbon": Fix(
        id="tie_ribbon",
        label="a neat bow",
        action="caught the ribbon and tied it into a neat little bow against the chair back",
        success="The ribbon stopped slapping the chair.",
        qa_text="tied the loose ribbon into a neat bow",
        tags={"repair", "ribbon"},
    ),
    "move_teacup": Fix(
        id="move_teacup",
        label="the side table",
        action="lifted the tiny teacup to the side table so the spoon could not ring on the chair arm",
        success="The spoon stopped bumping the cup by the chair.",
        qa_text="moved the teacup to the side table",
        tags={"repair", "teacup"},
    ),
}

SOURCE_TO_FIXES = {
    "rocker_joint": {"oil_joint"},
    "wind_chime": {"hang_chime"},
    "ribbon": {"tie_ribbon"},
    "teacup": {"move_teacup"},
}

HEROES = {
    "Pip": Animal(id="Pip", species_word="rabbit", type="rabbit_boy", trait="cautious", tags={"rabbit"}),
    "Mimi": Animal(id="Mimi", species_word="mouse", type="mouse_girl", trait="curious", tags={"mouse"}),
    "Tansy": Animal(id="Tansy", species_word="squirrel", type="squirrel_girl", trait="bright", tags={"squirrel"}),
    "Bram": Animal(id="Bram", species_word="hedgehog", type="hedgehog_girl", trait="cautious", tags={"hedgehog"}),
}

HELPERS = {
    "Moss": Animal(id="Moss", species_word="badger", type="badger_male", trait="patient", tags={"badger"}),
    "Fern": Animal(id="Fern", species_word="rabbit", type="rabbit_girl", trait="gentle", tags={"rabbit"}),
    "Hazel": Animal(id="Hazel", species_word="squirrel", type="squirrel_girl", trait="calm", tags={"squirrel"}),
}

KNOWLEDGE = {
    "breeze": [(
        "What is a breeze?",
        "A breeze is a soft, moving bit of air outside. It can push leaves, ribbons, or chimes and make them move."
    )],
    "rocking_chair": [(
        "What is a rocking chair?",
        "A rocking chair is a chair with curved runners under it, so it can rock back and forth. If one part gets loose, it may squeak or creak."
    )],
    "wind_chime": [(
        "What does a wind chime do?",
        "A wind chime hangs up and makes little sounds when the air moves it. The breeze can tap its pieces together."
    )],
    "teacup": [(
        "Why can a spoon make noise in a cup?",
        "If a spoon knocks the side of a cup, it makes a ringing sound. A small shake can turn into a ting-ting noise."
    )],
    "ribbon": [(
        "Why does a ribbon flap in the wind?",
        "A loose ribbon is light, so moving air can lift and slap it. That is why it can go flap-flap in a breeze."
    )],
    "repair": [(
        "What does it mean to fix something gently?",
        "It means you look closely at the real problem and do the small thing that helps. A careful fix stops the trouble without making a new one."
    )],
}
KNOWLEDGE_ORDER = ["breeze", "rocking_chair", "wind_chime", "teacup", "ribbon", "repair"]


@dataclass
class StoryParams:
    place: str
    chair: str
    source: str
    fix: str
    hero: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    chair = f["chair_cfg"]
    source = f["source_cfg"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "breeze", "chair", and "sunday", and uses sound effects like "{source.sound}".',
        f"Tell a gentle story where {hero.id} is frightened by a strange sound near a {chair.label}, but {helper.id} helps discover the true cause.",
        f"Write a cozy sunday animal tale with a breeze, a chair, a spooky little sound, and a calm ending that shows what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    chair = f["chair_cfg"]
    source = f["source_cfg"]
    fix = f["fix_cfg"]
    place = f["place_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.attrs['species_word']}, and {helper.id}, who helped on sunday. They were together near a {chair.label} in {place.label}."
        ),
        (
            f"Why did {hero.id} move away from the chair?",
            f"{hero.id} heard {source.sound} when the breeze touched something by the chair, and the noise felt spooky. That made {hero.pronoun('object')} worry there might be something hiding there."
        ),
        (
            "What was really making the sound?",
            f"It was {source.phrase}. The breeze kept moving it, so the sound happened again whenever the air puffed through."
        ),
        (
            f"How did {helper.id} solve the problem?",
            f"{helper.id} {fix.qa_text}. That was the right fix because it changed the very thing the breeze had been shaking."
        ),
        (
            "How did the story end?",
            f"In the end, {hero.id} climbed back into the chair and felt safe again. Another breeze came, but the spooky sound was gone, which proved the problem had changed."
        ),
    ]
    if f.get("brave_follow"):
        qa.append((
            f"Was {hero.id} brave?",
            f"Yes. {hero.id} felt worried at first, but still went to look with {helper.id}. That brave step helped {hero.pronoun('object')} learn the true cause."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"breeze", "repair"} | set(world.facts["chair_cfg"].tags) | set(world.facts["source_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="porch",
        chair="rocking",
        source="rocker_joint",
        fix="oil_joint",
        hero="Pip",
        helper="Moss",
    ),
    StoryParams(
        place="garden",
        chair="wicker",
        source="ribbon",
        fix="tie_ribbon",
        hero="Mimi",
        helper="Fern",
    ),
    StoryParams(
        place="porch",
        chair="wicker",
        source="teacup",
        fix="move_teacup",
        hero="Tansy",
        helper="Hazel",
    ),
    StoryParams(
        place="apple_tree",
        chair="folding",
        source="wind_chime",
        fix="hang_chime",
        hero="Bram",
        helper="Fern",
    ),
]


ASP_RULES = r"""
compatible_source(P,C,S) :- place(P), chair(C), source(S),
                            affords_chair(P,C), affords_source(P,S),
                            not blocked(P,C,S).

blocked(_,C,rocker_joint) :- C != rocking.
blocked(_,rocking,ribbon).
valid(P,C,S,F) :- compatible_source(P,C,S), fixes(S,F).

outcome(calm) :- chosen_source(S), chosen_fix(F), fixes(S,F).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for chair_id in sorted(place.chairs):
            lines.append(asp.fact("affords_chair", place_id, chair_id))
        for source_id in sorted(place.sources):
            lines.append(asp.fact("affords_source", place_id, source_id))
    for chair_id in CHAIRS:
        lines.append(asp.fact("chair", chair_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    for source_id, fixes in SOURCE_TO_FIXES.items():
        for fix_id in sorted(fixes):
            lines.append(asp.fact("fixes", source_id, fix_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        if asp_outcome(params) != "calm":
            rc = 1
            print(f"MISMATCH in ASP outcome for {params}.")
            break
    else:
        print(f"OK: ASP outcome matches curated stories ({len(CURATED)} checked).")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story or "sunday" not in sample.story or "chair" not in sample.story or "breeze" not in sample.story:
            raise StoryError("smoke test story missed required seed words")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a sunday breeze, a chair, and a small sound that gets explained."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--chair", choices=sorted(CHAIRS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.chair and args.source and not source_fits(args.place, args.chair, args.source):
        raise StoryError(explain_rejection(args.place, args.chair, args.source))
    if args.source and args.fix and not fix_works(args.source, args.fix):
        raise StoryError(explain_fix(args.source, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.chair is None or combo[1] == args.chair)
        and (args.source is None or combo[2] == args.source)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, chair_id, source_id, fix_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(HEROES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        place=place_id,
        chair=chair_id,
        source=source_id,
        fix=fix_id,
        hero=hero_id,
        helper=helper_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.chair not in CHAIRS:
        raise StoryError(f"(No story: unknown chair '{params.chair}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if params.hero not in HEROES:
        raise StoryError(f"(No story: unknown hero '{params.hero}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not source_fits(params.place, params.chair, params.source):
        raise StoryError(explain_rejection(params.place, params.chair, params.source))
    if not fix_works(params.source, params.fix):
        raise StoryError(explain_fix(params.source, params.fix))

    world = tell(
        place=PLACES[params.place],
        chair_cfg=CHAIRS[params.chair],
        source_cfg=SOURCES[params.source],
        fix_cfg=FIXES[params.fix],
        hero_cfg=HEROES[params.hero],
        helper_cfg=HELPERS[params.helper],
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
        print(f"{len(combos)} compatible (place, chair, source, fix) combos:\n")
        for place_id, chair_id, source_id, fix_id in combos:
            print(f"  {place_id:10} {chair_id:8} {source_id:12} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero} at {p.place}: {p.source} by the {p.chair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
