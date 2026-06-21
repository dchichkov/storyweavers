#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py
===============================================================

A standalone story world for a small nursery-rhyme-style tale about a child, a
clarinet, and the moral value of being kind enough to listen before making a
noise.

This domain models one simple pattern:

    a child longs to play a cheerful clarinet tune,
    someone nearby needs quiet,
    a warning is grounded in the world state,
    and the child either listens in time or learns to make amends kindly.

The world prefers plausible combinations only:
- the listener must fit the setting,
- the chosen gentle fix must actually protect that listener there.

Run it
------
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py --place cottage --listener baby --fix garden_path
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py --place meadow --listener baby
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/clarinet_moral_value_nursery_rhyme.py --verify
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
GENTLE_TRAITS = {"patient", "kind", "thoughtful", "careful"}


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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    hush_spot: str
    allowed_listeners: set[str] = field(default_factory=set)
    reachable_fixes: set[str] = field(default_factory=set)
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
class Listener:
    id: str
    label: str
    phrase: str
    need: str
    trouble: str
    settle: str
    protected_by: set[str] = field(default_factory=set)
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
    move_line: str
    ending_line: str
    helps: set[str] = field(default_factory=set)
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
class Tune:
    id: str
    title: str
    hum: str
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
        clone.facts = dict(self.facts)
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


def _r_disturb(world: World) -> list[str]:
    out: list[str] = []
    player = world.entities.get("hero")
    listener = world.entities.get("listener")
    place = world.entities.get("place")
    if player is None or listener is None or place is None:
        return out
    if player.meters["sound"] < THRESHOLD:
        return out
    if listener.attrs.get("protected", False):
        return out
    sig = ("disturb", listener.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.meters["disturbed"] += 1
    player.memes["guilt"] += 1
    place.meters["hush"] += 1
    out.append("__disturbed__")
    return out


def _r_concern(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    listener = world.entities.get("listener")
    if helper is None or listener is None:
        return out
    if listener.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("concern", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["concern"] += 1
    out.append("__concern__")
    return out


CAUSAL_RULES = [
    Rule(name="disturb", tag="physical", apply=_r_disturb),
    Rule(name="concern", tag="social", apply=_r_concern),
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


def listener_fits(place: Place, listener: Listener) -> bool:
    return listener.id in place.allowed_listeners


def fix_works(place: Place, listener: Listener, fix: Fix) -> bool:
    return fix.id in place.reachable_fixes and listener.id in fix.helps and fix.id in listener.protected_by


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for listener_id, listener in LISTENERS.items():
            if not listener_fits(place, listener):
                continue
            for fix_id, fix in FIXES.items():
                if fix_works(place, listener, fix):
                    combos.append((place_id, listener_id, fix_id))
    return combos


def initial_trait_meme(trait: str) -> float:
    return 5.0 if trait in GENTLE_TRAITS else 2.0


def would_listen_first(trait: str) -> bool:
    return trait in GENTLE_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "averted" if would_listen_first(params.trait) else "mended"


def predict_disturb(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["sound"] += 1
    propagate(sim, narrate=False)
    listener = sim.get("listener")
    return {
        "disturbed": listener.meters["disturbed"] >= THRESHOLD,
        "guilt": hero.memes["guilt"],
    }


def nursery_intro(world: World, hero: Entity, place: Place, tune: Tune) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {place.label}, where light was thin, little {hero.id} tucked {hero.pronoun('possessive')} clarinet under {hero.pronoun('possessive')} chin."
    )
    world.say(
        f"{place.opening} {hero.pronoun().capitalize()} longed to play {tune.title}, a bright small tune to skip the day along."
    )


def need_quiet(world: World, listener_cfg: Listener) -> None:
    listener = world.get("listener")
    world.say(
        f"But nearby rested {listener_cfg.phrase}, and {listener.pronoun('subject')} needed quiet because {listener_cfg.need}."
    )


def desire(world: World, hero: Entity, tune: Tune) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f'"Tum-ti-tum," sang {hero.id} softly to {hero.pronoun("self") if False else hero.pronoun("object")}, for the tune already danced in {hero.pronoun("possessive")} toes.'
    )


def warn(world: World, helper: Entity, hero: Entity, listener_cfg: Listener, fix: Fix) -> None:
    pred = predict_disturb(world)
    world.facts["predicted_disturbance"] = pred["disturbed"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} lifted one finger and said, "Hear first, play next, dear {hero.id}. If the clarinet starts here, {listener_cfg.trouble}."'
    )
    world.say(
        f'"Kind music can wait for the kinder place. We can {fix.move_line}."'
    )


def heed(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    hero.memes["kindness"] += 1
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} looked, and listened, and lowered the clarinet. Then {hero.pronoun()} nodded and took {helper.label_word}'s hand."
    )
    move_to_fix(world, hero, fix)
    gentle_play(world, hero)
    world.say(
        "Because a kind heart listened before it blew, no one was troubled, and the tune came out true."
    )


def ignore(world: World, hero: Entity, tune: Tune) -> None:
    hero.memes["haste"] += 1
    world.say(
        f"But {hero.id} was hasty. Up popped the clarinet, and out skipped {tune.hum} before another thought could settle."
    )
    hero.meters["sound"] += 1
    propagate(world, narrate=False)


def show_disturbance(world: World, listener_cfg: Listener) -> None:
    listener = world.get("listener")
    if listener_cfg.id == "baby":
        world.say("The baby blinked awake and gave a wobbly cry.")
    elif listener_cfg.id == "robin":
        world.say("The robin chicks gave a startled flutter in their nest.")
    elif listener_cfg.id == "grandpa":
        world.say("Grandpa opened his tired eyes and lost the little nap he had just found.")
    else:
        world.say(listener_cfg.trouble.capitalize() + ".")
    world.say(
        f"At once {world.get('hero').id} felt the wrongness of it, for merry music is not merry when it tumbles on someone else's rest."
    )


def apology(world: World, hero: Entity, helper: Entity, listener_cfg: Listener) -> None:
    hero.memes["guilt"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f'"Oh dear," whispered {hero.id}. "My clarinet was bright, but I was not thoughtful."'
    )
    world.say(
        f'{helper.label_word.capitalize()} gave a gentle squeeze. "{listener_cfg.settle}, and then let your tune be kind as well."'
    )


def move_to_fix(world: World, hero: Entity, fix: Fix) -> None:
    listener = world.get("listener")
    listener.attrs["protected"] = True
    world.facts["used_fix"] = fix.id
    world.say(
        f"So off they went to {fix.label}, step by step and light by light. {fix.move_line.capitalize()}."
    )


def gentle_play(world: World, hero: Entity) -> None:
    hero.meters["sound"] = 0.0
    hero.meters["soft_sound"] += 1
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1


def ending(world: World, hero: Entity, tune: Tune, listener_cfg: Listener, fix: Fix, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"There {hero.id} played {tune.ending}, and the clarinet curled through the air as softly as a ribbon."
        )
        world.say(
            f"Back by the first place, {listener_cfg.settle.lower()}, and the day stayed sweet. That was the moral under every note: kind children listen before they toot."
        )
    else:
        world.say(
            f"Soon the quiet came back, and then {hero.id} played {tune.ending} by {fix.label}, with gentler cheeks and wiser breath."
        )
        world.say(
            f"The clarinet sounded prettier then, because kindness had entered the song. That was the moral under every note: a merry heart must also be considerate."
        )
def tell(
    listener_cfg: Listener,
    fix: Fix,
    tune: Tune,
    hero_name: str,
    hero_type: HeroType,
    helper_type: HelperType,
    trait: Trait,
    place=None,
) -> World:
    world = World(place=place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[trait], attrs={}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper", attrs={}))
    listener_type = {
        "baby": "girl",
        "robin": "thing",
        "grandpa": "grandfather",
    }.get(listener_cfg.id, "thing")
    listener = world.add(Entity(id="listener", kind="character", type=listener_type, label=listener_cfg.label, role="listener", attrs={"protected": False}))
    clarinet = world.add(Entity(id="clarinet", kind="thing", type="instrument", label="clarinet", phrase="a shiny clarinet", attrs={}))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, attrs={}))

    hero.attrs["name"] = hero_name
    helper.attrs["relation"] = helper.label_word
    listener.attrs["need"] = listener_cfg.need
    hero.memes["gentleness"] = initial_trait_meme(trait)
    hero.meters["sound"] = 0.0
    listener.meters["disturbed"] = 0.0
    place_ent.meters["hush"] = 0.0

    nursery_intro(world, hero, place, tune)
    need_quiet(world, listener_cfg)

    world.para()
    desire(world, hero, tune)
    warn(world, helper, hero, listener_cfg, fix)

    outcome = outcome_of(
        StoryParams(
            place=place.id,
            listener=listener_cfg.id,
            fix=fix.id,
            tune=tune.id,
            name=hero_name,
            gender=hero_type,
            helper=helper_type,
            trait=trait,
            seed=None,
        )
    )

    world.para()
    if outcome == "averted":
        heed(world, hero, helper, fix)
    else:
        ignore(world, hero, tune)
        show_disturbance(world, listener_cfg)
        apology(world, hero, helper, listener_cfg)
        move_to_fix(world, hero, fix)
        gentle_play(world, hero)

    world.para()
    ending(world, hero, tune, listener_cfg, fix, outcome)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        helper=helper,
        listener=listener,
        listener_cfg=listener_cfg,
        place=place,
        fix=fix,
        tune=tune,
        clarinet=clarinet,
        outcome=outcome,
        disturbed=listener.meters["disturbed"] >= THRESHOLD,
        protected=listener.attrs.get("protected", False),
        moral="kind children listen before they play loudly",
    )
    return world
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


PLACES = {
    "cottage": Place(
        id="cottage",
        label="the little cottage",
        opening="By the window sat a pot of mint, and by the door lay a straw mat.",
        hush_spot="the garden path",
        allowed_listeners={"baby"},
        reachable_fixes={"garden_path", "wait_by_window"},
        tags={"home"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard lane",
        opening="The apples rocked like lanterns, and bees drew sleepy circles.",
        hush_spot="the gate by the lane",
        allowed_listeners={"grandpa"},
        reachable_fixes={"gate_lane", "wait_by_window"},
        tags={"orchard"},
    ),
    "willow_bank": Place(
        id="willow_bank",
        label="the willow bank",
        opening="Willow leaves trailed the stream, and reeds made a hush of their own.",
        hush_spot="the footbridge",
        allowed_listeners={"robin"},
        reachable_fixes={"footbridge", "wait_by_window"},
        tags={"stream"},
    ),
}

LISTENERS = {
    "baby": Listener(
        id="baby",
        label="baby",
        phrase="a drowsy baby in a cradle",
        need="a nap could finish its small work",
        trouble="the baby will wake and cry",
        settle="Let the baby drift back to sleep",
        protected_by={"garden_path", "wait_by_window"},
        tags={"baby", "sleep"},
    ),
    "robin": Listener(
        id="robin",
        label="robin chicks",
        phrase="three robin chicks in a willow nest",
        need="their little hearts were easiest with calm around them",
        trouble="the robin chicks will startle in the nest",
        settle="Let the chicks settle their feathers again",
        protected_by={"footbridge", "wait_by_window"},
        tags={"bird", "nest"},
    ),
    "grandpa": Listener(
        id="grandpa",
        label="grandpa",
        phrase="grandpa in his chair with a folded hat on his knees",
        need="his tired eyes had just begun to rest",
        trouble="grandpa will lose his nap",
        settle="Let grandpa close his eyes once more",
        protected_by={"gate_lane", "wait_by_window"},
        tags={"rest", "family"},
    ),
}

FIXES = {
    "garden_path": Fix(
        id="garden_path",
        label="the garden path",
        move_line="walk to the garden path beyond the cradle room",
        ending_line="played by the beans and marigolds",
        helps={"baby"},
        tags={"move_away", "garden"},
    ),
    "footbridge": Fix(
        id="footbridge",
        label="the footbridge",
        move_line="cross to the footbridge, away from the willow nest",
        ending_line="played above the stream where the water carried the notes",
        helps={"robin"},
        tags={"move_away", "bridge"},
    ),
    "gate_lane": Fix(
        id="gate_lane",
        label="the gate by the lane",
        move_line="step to the gate by the lane where the wind could take the sound",
        ending_line="played near the gate while the orchard stayed calm behind",
        helps={"grandpa"},
        tags={"move_away", "gate"},
    ),
    "wait_by_window": Fix(
        id="wait_by_window",
        label="the sunny window seat",
        move_line="wait by the sunny window until quiet no longer needed guarding",
        ending_line="played once the resting time was done",
        helps={"baby", "robin", "grandpa"},
        tags={"wait", "patience"},
    ),
}

TUNES = {
    "skip": Tune(
        id="skip",
        title="the skipping tune",
        hum="tip-ta tum, tip-ta tee",
        ending="the skipping tune, round and small",
        tags={"music"},
    ),
    "moon": Tune(
        id="moon",
        title="the moon-round tune",
        hum="loo-la loo, la-lay",
        ending="the moon-round tune, silver and slow",
        tags={"music"},
    ),
    "sunny": Tune(
        id="sunny",
        title="the sunny stair tune",
        hum="tum-ti-tum, tra-lay",
        ending="the sunny stair tune, bright but gentle",
        tags={"music"},
    ),
}

GIRL_NAMES = ["May", "Nell", "Mina", "Poppy", "Wren", "Tilly", "Elsie", "June"]
BOY_NAMES = ["Pip", "Toby", "Benji", "Milo", "Ned", "Rowan", "Kit", "Ollie"]
TRAITS = ["patient", "kind", "thoughtful", "careful", "hasty", "showy", "impulsive"]


KNOWLEDGE = {
    "clarinet": [
        (
            "What is a clarinet?",
            "A clarinet is a wind instrument. You blow through a mouthpiece and cover little holes or keys to make different notes."
        )
    ],
    "baby": [
        (
            "Why do babies need quiet for naps?",
            "Babies are still growing, and naps help their bodies and brains rest. A sudden loud sound can wake them before the rest is finished."
        )
    ],
    "bird": [
        (
            "Why can loud sounds startle baby birds?",
            "Baby birds are small and sensitive, so sudden noise can frighten them. Calm places help them feel safe in their nest."
        )
    ],
    "rest": [
        (
            "Why is rest important for older people too?",
            "Rest helps tired bodies feel stronger and calmer. A quiet nap can make an old person feel better afterward."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting without making a fuss. It helps you choose the right time instead of only the fastest time."
        )
    ],
    "kindness": [
        (
            "What does it mean to be considerate?",
            "Being considerate means thinking about how your actions feel to someone else. You do not only ask what you want, but also what others need."
        )
    ],
}

KNOWLEDGE_ORDER = ["clarinet", "baby", "bird", "rest", "patience", "kindness"]
@dataclass
class StoryParams:
    place: str
    listener: str
    fix: str
    tune: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="cottage",
        listener="baby",
        fix="garden_path",
        tune="skip",
        name="May",
        gender="girl",
        helper="mother",
        trait="patient",
        seed=1,
    ),
    StoryParams(
        place="willow_bank",
        listener="robin",
        fix="footbridge",
        tune="moon",
        name="Pip",
        gender="boy",
        helper="father",
        trait="hasty",
        seed=2,
    ),
    StoryParams(
        place="orchard",
        listener="grandpa",
        fix="gate_lane",
        tune="sunny",
        name="Nell",
        gender="girl",
        helper="grandmother",
        trait="thoughtful",
        seed=3,
    ),
    StoryParams(
        place="cottage",
        listener="baby",
        fix="wait_by_window",
        tune="moon",
        name="Milo",
        gender="boy",
        helper="mother",
        trait="showy",
        seed=4,
    ),
    StoryParams(
        place="willow_bank",
        listener="robin",
        fix="wait_by_window",
        tune="skip",
        name="Wren",
        gender="girl",
        helper="father",
        trait="careful",
        seed=5,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    listener_cfg = f["listener_cfg"]
    tune = f["tune"]
    fix = f["fix"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "clarinet" and teaches a moral value.',
        f"Tell a gentle story about a {hero.type} named {f['hero_name']} who wants to play a clarinet tune, but someone nearby needs quiet, so the child must learn to be considerate.",
        f"Write a small rhyming tale where {listener_cfg.label} needs peace, the child chooses {fix.label}, and the ending shows that kindness can make {tune.title} sound sweeter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    listener_cfg = f["listener_cfg"]
    tune = f["tune"]
    fix = f["fix"]
    outcome = f["outcome"]
    listener_name = listener_cfg.label

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a child with a clarinet, and {helper.label_word}, who helps {hero.pronoun('object')} choose a kinder way to play."
        ),
        (
            "Why could the clarinet not be played there right away?",
            f"It could not be played there right away because {listener_cfg.phrase} needed quiet. A loud clarinet would disturb that rest, so the warning was about being considerate."
        ),
        (
            f"What kinder plan did {f['hero_name']} use?",
            f"{f['hero_name']} used {fix.label}. That plan protected {listener_name} first and gave the music a better place or time to be heard."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How did {f['hero_name']} show the moral value in the story?",
                f"{f['hero_name']} listened before playing and chose patience over haste. That kept anyone from being upset, and it showed that kindness can guide even a cheerful song."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {f['hero_name']} played too soon, and what changed after that?",
                f"{f['hero_name']} played too soon, and {listener_name} was disturbed. Then {hero.pronoun().capitalize()} felt sorry, made things right, and moved the music so the clarinet could be kind as well as merry."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            "The moral is that you should think about other people before doing something noisy. Music is happiest when it does not trample someone else's need for quiet."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"clarinet", "kindness"}
    listener_id = f["listener_cfg"].id
    fix_id = f["fix"].id
    if listener_id == "baby":
        tags.add("baby")
    if listener_id == "robin":
        tags.add("bird")
    if listener_id == "grandpa":
        tags.add("rest")
    if fix_id == "wait_by_window":
        tags.add("patience")
    else:
        tags.add("patience")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, listener: Listener, fix: Optional[Fix] = None) -> str:
    if not listener_fits(place, listener):
        allowed = ", ".join(sorted(place.allowed_listeners))
        return (
            f"(No story: {listener.label} does not naturally belong in {place.label}. "
            f"This place supports listeners like: {allowed}.)"
        )
    if fix is not None and not fix_works(place, listener, fix):
        return (
            f"(No story: {fix.label} does not really protect {listener.label} in {place.label}. "
            f"Pick a fix that gives the needed quiet.)"
        )
    return "(No story: this combination does not make a reasonable quiet-and-kindness tale.)"


def _pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


ASP_RULES = r"""
listener_fits(P,L) :- allows(P,L).
fix_works(P,L,F) :- reachable(P,F), helps(F,L), protects(L,F).
valid(P,L,F) :- place(P), listener(L), fix(F), listener_fits(P,L), fix_works(P,L,F).

gentle(T) :- trait(T), gentle_trait(T).
outcome(averted) :- chosen_trait(T), gentle(T).
outcome(mended) :- chosen_trait(T), not gentle(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for listener_id in sorted(place.allowed_listeners):
            lines.append(asp.fact("allows", place_id, listener_id))
        for fix_id in sorted(place.reachable_fixes):
            lines.append(asp.fact("reachable", place_id, fix_id))
    for listener_id, listener in LISTENERS.items():
        lines.append(asp.fact("listener", listener_id))
        for fix_id in sorted(listener.protected_by):
            lines.append(asp.fact("protects", listener_id, fix_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for listener_id in sorted(fix.helps):
            lines.append(asp.fact("helps", fix_id, listener_id))
    for tune_id in TUNES:
        lines.append(asp.fact("tune", tune_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(GENTLE_TRAITS):
        lines.append(asp.fact("gentle_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_trait", params.trait)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a child, a clarinet, and the moral value of considerate music."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.listener:
        place = PLACES[args.place]
        listener = LISTENERS[args.listener]
        if not listener_fits(place, listener):
            raise StoryError(explain_rejection(place, listener))
    if args.place and args.listener and args.fix:
        place = PLACES[args.place]
        listener = LISTENERS[args.listener]
        fix = FIXES[args.fix]
        if not fix_works(place, listener, fix):
            raise StoryError(explain_rejection(place, listener, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.listener is None or combo[1] == args.listener)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, listener_id, fix_id = rng.choice(sorted(combos))
    tune_id = args.tune or rng.choice(sorted(TUNES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        listener=listener_id,
        fix=fix_id,
        tune=tune_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.listener not in LISTENERS:
        raise StoryError(f"(Unknown listener: {params.listener})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.tune not in TUNES:
        raise StoryError(f"(Unknown tune: {params.tune})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.helper not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    place = PLACES[params.place]
    listener = LISTENERS[params.listener]
    fix = FIXES[params.fix]
    if not listener_fits(place, listener):
        raise StoryError(explain_rejection(place, listener))
    if not fix_works(place, listener, fix):
        raise StoryError(explain_rejection(place, listener, fix))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        listener_cfg=LISTENERS[params.listener],
        fix=FIXES[params.fix],
        tune=TUNES[params.tune],
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome(s) differ.")
        for bad in mismatches[:5]:
            print(" ", bad)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        sample2 = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not sample2.story.strip():
            raise StoryError("Random generated story was empty.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, listener, fix) combos:\n")
        for place, listener, fix in combos:
            print(f"  {place:11} {listener:8} {fix}")
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
            header = f"### {p.name}: clarinet at {p.place} for {p.listener} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
