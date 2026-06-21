#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py
====================================================================================

A standalone storyworld about a bedtime superhero mystery: a child hero's beloved
plush sidekick goes missing just as a family hound lets out a lonely howl during
a lullaby. The sound creates a misunderstanding, the child searches for clues,
and the mystery is solved in a gentle, state-driven way.

The world models:
- physical meters: missing, howling, found, carried, snagged
- emotional memes: joy, worry, suspicion, patience, relief, trust, apology

Reasonableness constraints:
- some mysteries only work for plush toys with a cape loop or ribbon
- some mysteries require a gentle hound that would plausibly carry a plush
- every generated combination must produce a solvable clue trail

Run it
------
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py --mystery laundry_basket
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py --plush moon_cat --mystery laundry_basket
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/hound_plush_lullaby_misunderstanding_mystery_to_solve.py --qa --json
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class HeroTheme:
    id: str
    title: str
    boast: str
    mission_word: str
    finishing_image: str
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
class PlushCfg:
    id: str
    label: str
    phrase: str
    partner_name: str
    power: str
    has_loop: bool = False
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
class HoundCfg:
    id: str
    breed_word: str
    call: str
    nature: str
    gentle_carry: bool = False
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
class Mystery:
    id: str
    room: str
    hiding_place: str
    clue: str
    suspect_story: str
    real_story: str
    reveal_text: str
    ending_image: str
    requires_loop: bool = False
    needs_gentle_hound: bool = False
    hound_role: str = "witness"  # witness | carrier
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


def _r_missing_worry(world: World) -> list[str]:
    hero = world.get("hero")
    plush = world.get("plush")
    sig = ("missing_worry",)
    if plush.meters["missing"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["worry"] += 1
    return []


def _r_howl_suspicion(world: World) -> list[str]:
    hero = world.get("hero")
    plush = world.get("plush")
    hound = world.get("hound")
    sig = ("howl_suspicion",)
    if (
        plush.meters["missing"] >= THRESHOLD
        and hound.meters["howling"] >= THRESHOLD
        and sig not in world.fired
    ):
        world.fired.add(sig)
        hero.memes["suspicion"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    plush = world.get("plush")
    sig = ("found_relief",)
    if plush.meters["found"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="howl_suspicion", tag="emotional", apply=_r_howl_suspicion),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
            world.say(s)
    return produced


def mystery_works(plush: PlushCfg, hound: HoundCfg, mystery: Mystery) -> bool:
    if mystery.requires_loop and not plush.has_loop:
        return False
    if mystery.needs_gentle_hound and not hound.gentle_carry:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for plush_id, plush in PLUSHES.items():
            for hound_id, hound in HOUNDS.items():
                for mystery_id, mystery in MYSTERIES.items():
                    if mystery_works(plush, hound, mystery):
                        combos.append((theme_id, plush_id, hound_id, mystery_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.trait in {"patient", "careful", "kind"}:
        return "investigates_first"
    return "accuses_first"


def predict_suspicion(world: World) -> dict:
    sim = world.copy()
    sim.get("plush").meters["missing"] += 1
    sim.get("hound").meters["howling"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("hero").memes["worry"],
        "suspicion": sim.get("hero").memes["suspicion"],
    }


def bedroom_setup(world: World, hero: Entity, helper: Entity, theme: HeroTheme, plush: Entity) -> None:
    hero.memes["joy"] += 1
    plush.memes["beloved"] += 1
    world.say(
        f"At bedtime, {hero.id} was not just a child. {hero.pronoun().capitalize()} was "
        f"{theme.title}, and {plush.label} was the plush partner called {plush.attrs['partner_name']}."
    )
    world.say(
        f"Together they had spent the evening {theme.boast}. Now the room was dim, "
        f"the blanket made a secret cape-cave, and it was time to rest."
    )
    world.say(
        f"{helper.label_word.capitalize()} sat by the bed and began a soft lullaby, the sort "
        f"that made the whole house feel slower and warmer."
    )


def vanishing(world: World, hero: Entity, plush: Entity, hound: Entity) -> None:
    plush.meters["missing"] += 1
    hound.meters["howling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached for {plush.label}, the bed was empty. "
        f"{plush.attrs['partner_name']} was gone."
    )
    world.say(
        f"Just then the family hound let out {hound.attrs['call']}, a long sleepy sound "
        f"from the hallway."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, hound: Entity, mystery: Mystery, trait: str) -> None:
    pred = predict_suspicion(world)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_suspicion"] = pred["suspicion"]
    if trait in {"impulsive", "dramatic", "bold"}:
        hero.memes["accusation"] += 1
        world.say(
            f"{hero.id} sat up so fast the blanket-cape slipped off one shoulder. "
            f'"That howl was a clue!" {hero.pronoun()} gasped. "{mystery.suspect_story}"'
        )
        world.say(
            f"{helper.label_word.capitalize()} did not scold. {helper.pronoun().capitalize()} only said, "
            f'"Maybe. But real heroes look for clues before they blame anyone."'
        )
    else:
        world.say(
            f"{hero.id}'s eyes grew wide, but {hero.pronoun()} held still and listened to the end "
            f"of the lullaby. The howl sounded suspicious, yet {helper.label_word} reminded "
            f"{hero.pronoun('object')} that mysteries need patient eyes."
        )


def investigate(world: World, hero: Entity, helper: Entity, plush: Entity, hound: Entity, mystery: Mystery) -> None:
    hero.memes["bravery"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"So {theme_phrase(world)} began a midnight {world.facts['theme'].mission_word}. "
        f"{hero.id} slid out of bed, {helper.label_word} carried a small lamp, and the hound "
        f"padded after them with worried ears."
    )
    world.say(
        f"In the {mystery.room}, they found the first clue: {mystery.clue}."
    )
    world.say(
        f"That clue changed the feeling in the room. It did not look like a villain's trail. "
        f"It looked like something small and ordinary had happened in the dark."
    )


def reveal(world: World, hero: Entity, helper: Entity, plush: Entity, hound: Entity, mystery: Mystery) -> None:
    plush.meters["found"] += 1
    propagate(world, narrate=False)
    if mystery.hound_role == "carrier":
        hound.meters["carried"] += 1
    else:
        hound.meters["witness"] += 1
    world.say(mystery.reveal_text.format(
        hero=hero.id,
        helper=helper.label_word,
        plush=plush.label,
        partner=plush.attrs["partner_name"],
        hound="hound",
    ))
    world.say(
        mystery.real_story.format(
            hero=hero.id,
            helper=helper.label_word,
            plush=plush.label,
            partner=plush.attrs["partner_name"],
            hound="hound",
        )
    )


def resolution(world: World, hero: Entity, helper: Entity, plush: Entity, hound: Entity, theme: HeroTheme, mystery: Mystery) -> None:
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    if hero.memes["accusation"] >= THRESHOLD:
        hero.memes["apology"] += 1
        world.say(
            f"{hero.id} hugged {plush.label} tight and looked at the hound. "
            f'"Sorry, brave hound," {hero.pronoun()} said. "I solved the mystery, and I guessed wrong first."'
        )
    else:
        world.say(
            f"{hero.id} knelt beside the hound and rubbed the soft ears between "
            f"{hero.pronoun('possessive')} fingers. The mystery was solved without any blaming at all."
        )
    world.say(
        f"{helper.label_word.capitalize()} tucked {plush.attrs['partner_name']} under {hero.id}'s arm and finished the lullaby. "
        f"This time the song felt different: not sleepy and worried, but sleepy and proud."
    )
    world.say(
        f"Back in bed, {hero.id} whispered that even superheroes need clues, patience, and kind hearts. "
        f"By the time the last note faded, {theme.finishing_image} and {mystery.ending_image}"
    )


def theme_phrase(world: World) -> str:
    return world.facts["theme"].title
def tell(
    hero_name: str,
    hero_gender: str,
    helper_type: HelperType,
    trait: Trait,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        attrs={},
    ))
    hound = world.add(Entity(
        id="hound",
        kind="character",
        type="hound",
        label="the hound",
        role="hound",
        traits=[hound_cfg.nature],
        attrs={"call": hound_cfg.call, "breed_word": hound_cfg.breed_word},
    ))
    plush = world.add(Entity(
        id="plush",
        kind="thing",
        type="plush",
        label=plush_cfg.phrase,
        role="plush",
        attrs={
            "partner_name": plush_cfg.partner_name,
            "power": plush_cfg.power,
            "has_loop": plush_cfg.has_loop,
        },
    ))

    hero.attrs["name"] = hero_name
    helper.attrs["name"] = helper.label_word
    world.facts.update(
        hero=hero,
        helper=helper,
        hound=hound,
        plush=plush,
        theme=theme,
        plush_cfg=plush_cfg,
        hound_cfg=hound_cfg,
        mystery=mystery,
        trait=trait,
    )
    hero.memes["patience"] = 2.0 if trait in {"patient", "careful", "kind"} else 0.0
    hero.memes["confidence"] = 1.0
    helper.memes["calm"] = 1.0
    hound.memes["sleepy"] = 1.0
    propagate(world, narrate=False)

    bedroom_setup(world, hero, helper, theme, plush)
    world.para()
    vanishing(world, hero, plush, hound)
    misunderstanding(world, hero, helper, hound, mystery, trait)
    world.para()
    investigate(world, hero, helper, plush, hound, mystery)
    reveal(world, hero, helper, plush, hound, mystery)
    world.para()
    resolution(world, hero, helper, plush, hound, theme, mystery)

    world.facts["outcome"] = outcome_of(StoryParams(
        theme=theme.id,
        plush=plush_cfg.id,
        hound=hound_cfg.id,
        mystery=mystery.id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper=helper_type,
        trait=trait,
        seed=None,
    ))
    world.facts["accused"] = hero.memes["accusation"] >= THRESHOLD
    world.facts["apologized"] = hero.memes["apology"] >= THRESHOLD
    return world
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


THEMES = {
    "moon_guard": HeroTheme(
        id="moon_guard",
        title="Moon Guard",
        boast="guarding the window from sneaky shadows",
        mission_word="moon mission",
        finishing_image="the blanket-cape lay smooth as silver armor",
    ),
    "comet_scout": HeroTheme(
        id="comet_scout",
        title="Comet Scout",
        boast="patrolling the room for invisible meteors",
        mission_word="comet mission",
        finishing_image="the pillow glowed like a quiet little cloud above a launch pad",
    ),
    "star_shield": HeroTheme(
        id="star_shield",
        title="Star Shield",
        boast="defending bedtime from imaginary space fog",
        mission_word="star mission",
        finishing_image="the night-light made a round gold shield on the wall",
    ),
}

PLUSHES = {
    "rocket_pup": PlushCfg(
        id="rocket_pup",
        label="rocket pup",
        phrase="a plush rocket pup",
        partner_name="Captain Puff",
        power="zooming through moon smoke",
        has_loop=True,
        tags={"plush", "loop"},
    ),
    "moon_cat": PlushCfg(
        id="moon_cat",
        label="moon cat",
        phrase="a plush moon cat",
        partner_name="Mittens Meteor",
        power="seeing in soft dark corners",
        has_loop=False,
        tags={"plush"},
    ),
    "thunder_bear": PlushCfg(
        id="thunder_bear",
        label="thunder bear",
        phrase="a plush thunder bear",
        partner_name="Boom-Bear",
        power="being brave during storms",
        has_loop=True,
        tags={"plush", "loop"},
    ),
}

HOUNDS = {
    "basset": HoundCfg(
        id="basset",
        breed_word="basset hound",
        call='"aroooo"',
        nature="droopy and gentle",
        gentle_carry=True,
        tags={"hound", "gentle"},
    ),
    "foxhound": HoundCfg(
        id="foxhound",
        breed_word="young hound",
        call='"awooo"',
        nature="busy and curious",
        gentle_carry=False,
        tags={"hound"},
    ),
    "coonhound": HoundCfg(
        id="coonhound",
        breed_word="big hound",
        call='"oooonh"',
        nature="sleepy and loyal",
        gentle_carry=True,
        tags={"hound", "gentle"},
    ),
}

MYSTERIES = {
    "dog_bed": Mystery(
        id="dog_bed",
        room="hallway nook",
        hiding_place="the hound's bed",
        clue="a soft dent in the dog bed and one bit of plush fur caught on the edge",
        suspect_story="The hound took my partner!",
        real_story="{helper.capitalize()} lifted the blanket from the dog bed, and there was {plush}, tucked in beside one floppy ear.",
        reveal_text="{helper} blinked, then smiled. \"Here is {partner}.\"",
        ending_image="the hound snored with one paw over the edge of the bed like a tired guard dog.",
        needs_gentle_hound=True,
        hound_role="carrier",
        tags={"hound", "dog_bed"},
    ),
    "laundry_basket": Mystery(
        id="laundry_basket",
        room="bathroom doorway",
        hiding_place="the laundry basket",
        clue="a tiny ribbon thread leading up to a basket full of warm towels",
        suspect_story="The hound must have chased my partner down the hall!",
        real_story="Nothing wicked had happened at all. {partner}'s loop had snagged on the laundry basket, and {plush} had tumbled in among the towels while the hound only howled along with the lullaby.",
        reveal_text="{helper.capitalize()} followed the thread and found {plush} peeking out from the towels.",
        ending_image="the basket looked much less mysterious once a plush paw was sticking over the rim.",
        requires_loop=True,
        hound_role="witness",
        tags={"laundry", "loop"},
    ),
    "rocking_chair": Mystery(
        id="rocking_chair",
        room="reading corner",
        hiding_place="under the rocking chair cushion",
        clue="the rocking chair still swaying a little and one plush ear poking from the seam",
        suspect_story="The hound hid my partner when it heard the lullaby!",
        real_story="{partner} had slid into the chair cushion when the rocker moved. The hound had come to listen to the lullaby too, and its howl was only a sleepy song, not a confession.",
        reveal_text="In the reading corner, {hero} saw a small plush ear under the rocking chair cushion and reached in for {plush}.",
        ending_image="the rocking chair rested at last, and the room felt friendly again.",
        hound_role="witness",
        tags={"chair", "lullaby"},
    ),
}


GIRL_NAMES = ["Nova", "Luna", "Zara", "Mia", "Ava", "Skye", "Ruby", "Nora"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Noah", "Jack", "Ben"]
TRAITS = ["patient", "careful", "kind", "impulsive", "dramatic", "bold"]


KNOWLEDGE = {
    "hound": [
        (
            "What is a hound?",
            "A hound is a kind of dog. Many hounds have strong noses and loud voices, so their howls can sound big even when they are gentle."
        )
    ],
    "plush": [
        (
            "What is a plush toy?",
            "A plush toy is a soft stuffed toy made for hugging. Children often keep one nearby because it feels safe and familiar."
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a quiet song sung to help someone feel calm and sleepy. Its soft rhythm can make a room feel peaceful."
        )
    ],
    "mystery": [
        (
            "What does it mean to solve a mystery?",
            "Solving a mystery means looking for clues and figuring out what really happened. Good clues help you replace a guess with the truth."
        )
    ],
    "apology": [
        (
            "Why should you apologize if you blame someone by mistake?",
            "An apology helps mend hurt feelings when your guess was unfair. It shows that telling the truth matters more than winning an argument."
        )
    ],
}
KNOWLEDGE_ORDER = ["hound", "plush", "lullaby", "mystery", "apology"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    theme = world.facts["theme"]
    plush_cfg = world.facts["plush_cfg"]
    mystery = world.facts["mystery"]
    return [
        f'Write a superhero bedtime story for a 3-to-5-year-old that includes the words "hound", "plush", and "lullaby".',
        f"Tell a gentle mystery where {hero.attrs['name']} plays {theme.title}, loses {plush_cfg.phrase}, hears a hound during a lullaby, and solves the misunderstanding with clues.",
        f"Write a short story with a misunderstanding and a mystery to solve, ending when a child hero discovers why a missing plush was really in {mystery.hiding_place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    plush_cfg = world.facts["plush_cfg"]
    mystery = world.facts["mystery"]
    hound_cfg = world.facts["hound_cfg"]
    outcome = world.facts["outcome"]
    hero_name = hero.attrs["name"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child pretending to be {world.facts['theme'].title}, plus a beloved plush partner and the family hound. The bedtime mystery begins when the plush goes missing during a lullaby."
        ),
        (
            f"Why did {hero_name} think the hound was part of the mystery?",
            f"The plush disappeared at the same moment the hound howled, so the two things seemed connected. That timing made the howl feel like a clue, even before {hero_name} knew what had really happened."
        ),
        (
            "How was the mystery solved?",
            f"They walked out with a lamp and followed a real clue: {mystery.clue}. That clue led them to {mystery.hiding_place}, where the missing plush was found."
        ),
    ]
    if outcome == "accuses_first":
        qa.append(
            (
                f"Did {hero_name} misunderstand the hound?",
                f"Yes. {hero_name} guessed the hound had taken the plush, but the clue trail showed a different truth. After the mystery was solved, {hero.pronoun()} apologized because the first guess had been unfair."
            )
        )
    else:
        qa.append(
            (
                f"What helped {hero_name} avoid blaming the hound too quickly?",
                f"{hero.pronoun('possessive').capitalize()} helper reminded {hero.pronoun('object')} to look for clues before blaming anyone. That patient choice turned a scary guess into a solvable mystery."
            )
        )
    qa.append(
        (
            f"What was the hound really doing?",
            f"In this story the {hound_cfg.breed_word} was not being mean at all. {mystery.real_story.format(hero=hero_name, helper=helper_word, plush=plush_cfg.phrase, partner=plush_cfg.partner_name, hound='hound')}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hound", "plush", "lullaby", "mystery"}
    if world.facts.get("apologized"):
        tags.add("apology")
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
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    theme: str
    plush: str
    hound: str
    mystery: str
    hero_name: str
    hero_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        theme="moon_guard",
        plush="rocket_pup",
        hound="basset",
        mystery="dog_bed",
        hero_name="Nova",
        hero_gender="girl",
        helper="mother",
        trait="impulsive",
        seed=1,
    ),
    StoryParams(
        theme="comet_scout",
        plush="thunder_bear",
        hound="coonhound",
        mystery="laundry_basket",
        hero_name="Leo",
        hero_gender="boy",
        helper="father",
        trait="careful",
        seed=2,
    ),
    StoryParams(
        theme="star_shield",
        plush="moon_cat",
        hound="foxhound",
        mystery="rocking_chair",
        hero_name="Mia",
        hero_gender="girl",
        helper="mother",
        trait="patient",
        seed=3,
    ),
]


def explain_rejection(plush: PlushCfg, hound: HoundCfg, mystery: Mystery) -> str:
    if mystery.requires_loop and not plush.has_loop:
        return (
            f"(No story: {plush.phrase} has no loop or ribbon to snag, so the "
            f"{mystery.id} mystery has no honest clue trail.)"
        )
    if mystery.needs_gentle_hound and not hound.gentle_carry:
        return (
            f"(No story: this mystery needs a gentle hound that would plausibly carry "
            f"a plush toy without ruining it. Try a softer hound choice.)"
        )
    return "(No story: that combination does not make a clear bedtime mystery.)"


ASP_RULES = r"""
valid(T, P, H, M) :- theme(T), plush(P), hound(H), mystery(M),
                     mystery_ok(P, H, M).

mystery_ok(P, _, M) :- mystery(M), not requires_loop(M), plush(P).
mystery_ok(P, _, M) :- mystery(M), requires_loop(M), plush_has_loop(P).
mystery_ok(P, H, M) :- mystery(M), needs_gentle_hound(M), gentle_hound(H),
                       (not requires_loop(M); plush_has_loop(P)).
mystery_ok(P, H, M) :- mystery(M), not needs_gentle_hound(M),
                       hound(H), (not requires_loop(M); plush_has_loop(P)).

accuses_first :- trait(impulsive).
accuses_first :- trait(dramatic).
accuses_first :- trait(bold).

outcome(accuses_first) :- accuses_first.
outcome(investigates_first) :- not accuses_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for plush_id, plush in PLUSHES.items():
        lines.append(asp.fact("plush", plush_id))
        if plush.has_loop:
            lines.append(asp.fact("plush_has_loop", plush_id))
    for hound_id, hound in HOUNDS.items():
        lines.append(asp.fact("hound", hound_id))
        if hound.gentle_carry:
            lines.append(asp.fact("gentle_hound", hound_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        if mystery.requires_loop:
            lines.append(asp.fact("requires_loop", mystery_id))
        if mystery.needs_gentle_hound:
            lines.append(asp.fact("needs_gentle_hound", mystery_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story during smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero bedtime misunderstanding and a mystery to solve."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--plush", choices=PLUSHES)
    ap.add_argument("--hound", choices=HOUNDS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plush and args.hound and args.mystery:
        if not mystery_works(PLUSHES[args.plush], HOUNDS[args.hound], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(PLUSHES[args.plush], HOUNDS[args.hound], MYSTERIES[args.mystery]))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.plush is None or c[1] == args.plush)
        and (args.hound is None or c[2] == args.hound)
        and (args.mystery is None or c[3] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, plush_id, hound_id, mystery_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        plush=plush_id,
        hound=hound_id,
        mystery=mystery_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.plush not in PLUSHES:
        raise StoryError(f"(Unknown plush: {params.plush})")
    if params.hound not in HOUNDS:
        raise StoryError(f"(Unknown hound: {params.hound})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if not mystery_works(PLUSHES[params.plush], HOUNDS[params.hound], MYSTERIES[params.mystery]):
        raise StoryError(explain_rejection(PLUSHES[params.plush], HOUNDS[params.hound], MYSTERIES[params.mystery]))

    world = tell(
        THEMES[params.theme],
        PLUSHES[params.plush],
        HOUNDS[params.hound],
        MYSTERIES[params.mystery],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
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
        print(f"{len(combos)} compatible (theme, plush, hound, mystery) combos:\n")
        for theme_id, plush_id, hound_id, mystery_id in combos:
            print(f"  {theme_id:12} {plush_id:13} {hound_id:10} {mystery_id}")
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
            header = f"### {p.hero_name}: {p.mystery} with {p.hound} and {p.plush} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
