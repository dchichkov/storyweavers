#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py
=====================================================================

A standalone story world for a tall-tale feast where a child boasts about a
mighty lute, a wobbling dessert with many layer upon layer of filling stands
nearby, and a plain napkin becomes the sensible fix.

This world models one small domain:

    a child boasts that louder music is better ->
    a helper predicts the loud tune will shake a tall treat ->
    a folded napkin can soften the lute and make the music gentle enough ->
    the ending proves the moral value: humility and honesty beat empty bragging

Run it
------
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py --place fair --tune thunder_reel --stack layer_cake
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py --stack stone_pie
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/layer_lute_napkin_moral_value_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman", "aunt", "mother", "sister", "cousin_girl"}
        male = {"boy", "man", "uncle", "father", "brother", "cousin_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    image: str
    echo: int
    boast: str
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
    label: str
    brag: str
    play: str
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
class Stack:
    id: str
    label: str
    phrase: str
    image: str
    steady: int
    wobbly: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class NapkinCfg:
    id: str
    label: str
    phrase: str
    muffle: int
    sturdy: int
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


def effective_sound(world: World) -> int:
    tune = world.facts["tune"]
    place = world.facts["place"]
    napkin = world.facts["napkin_cfg"]
    using_napkin = world.facts.get("using_napkin", False)
    return max(0, tune.loudness + place.echo - (napkin.muffle if using_napkin else 0))


def _r_wobble(world: World) -> list[str]:
    stack_ent = world.get("stack")
    if not world.facts["stack_cfg"].wobbly:
        return []
    if world.get("lute").meters["sound"] < THRESHOLD:
        return []
    sound = int(world.get("lute").meters["sound"])
    steady = world.facts["stack_cfg"].steady
    if sound < steady:
        return []
    sig = ("wobble", sound)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stack_ent.meters["wobble"] += 1
    for eid in ("hero", "helper"):
        world.get(eid).memes["worry"] += 1
    return ["__wobble__"]


def _r_slide(world: World) -> list[str]:
    stack_ent = world.get("stack")
    if stack_ent.meters["wobble"] < THRESHOLD:
        return []
    sound = int(world.get("lute").meters["sound"])
    steady = world.facts["stack_cfg"].steady
    if sound < steady + 1:
        return []
    sig = ("slide", sound)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stack_ent.meters["slid"] += 1
    stack_ent.meters["mess"] += 1
    world.get("hero").memes["shame"] += 1
    world.get("helper").memes["concern"] += 1
    return ["__slide__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="slide", tag="physical", apply=_r_slide),
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
        for line in produced:
            world.say(line)
    return produced


def hazard(place: Place, tune: Tune, stack: Stack) -> bool:
    return stack.wobbly and (tune.loudness + place.echo) >= stack.steady


def napkin_works(place: Place, tune: Tune, stack: Stack, napkin: NapkinCfg) -> bool:
    if not stack.wobbly:
        return False
    if napkin.sturdy <= 0:
        return False
    loud = tune.loudness + place.echo
    return max(0, loud - napkin.muffle) < stack.steady and napkin.sturdy >= max(1, loud - stack.steady + 1)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for tune_id, tune in TUNES.items():
            for stack_id, stack in STACKS.items():
                for napkin_id, napkin in NAPKINS.items():
                    if hazard(place, tune, stack) and napkin_works(place, tune, stack, napkin):
                        combos.append((place_id, tune_id, stack_id, napkin_id))
    return combos


def would_heed(relation: str, helper_age: int, hero_age: int, trait: str) -> bool:
    if trait in {"humble", "careful", "steady"}:
        return True
    older_helper = relation in {"siblings", "cousins"} and helper_age > hero_age
    return older_helper and trait == "showy"


def predict_stack(world: World) -> dict:
    sim = world.copy()
    sim.facts["using_napkin"] = False
    sim.get("lute").meters["sound"] = float(effective_sound(sim))
    propagate(sim, narrate=False)
    safe = world.copy()
    safe.facts["using_napkin"] = True
    safe.get("lute").meters["sound"] = float(effective_sound(safe))
    propagate(safe, narrate=False)
    return {
        "unsafe_sound": int(sim.get("lute").meters["sound"]),
        "unsafe_wobble": sim.get("stack").meters["wobble"] >= THRESHOLD,
        "unsafe_slide": sim.get("stack").meters["slid"] >= THRESHOLD,
        "safe_sound": int(safe.get("lute").meters["sound"]),
        "safe_wobble": safe.get("stack").meters["wobble"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place, stack: Stack) -> None:
    world.say(
        f"On the biggest feast day that {place.label} had seen in a hundred windy years, "
        f"{hero.id} and {helper.id} came to the tables at dawn. {place.image}"
    )
    world.say(
        f"In the middle stood {stack.phrase}, {stack.image}"
    )


def boast(world: World, hero: Entity, place: Place, tune: Tune) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} carried a lute almost as long as a canoe and grinned at the crowd. "
        f'"I can play {tune.label} so strong that {place.boast}!"'
    )
    world.say(
        f"That was tall-tale talk, and it made {hero.id}'s chest feel two buttons wider."
    )


def helper_warning(world: World, helper: Entity, hero: Entity, napkin: NapkinCfg, stack: Stack) -> None:
    pred = predict_stack(world)
    world.facts["predicted"] = pred
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} looked from the lute to {stack.the} and saw trouble before it happened. "
        f'"If you thunder away, the table will dance and the top will slide," {helper.pronoun()} said.'
    )
    world.say(
        f'"Fold {napkin.phrase} under the lute strings and play near the cake instead of at the clouds. '
        f'True music does not need to shout."'
    )


def accept_advice(world: World, hero: Entity, napkin: NapkinCfg) -> None:
    world.facts["using_napkin"] = True
    world.get("napkin").meters["used"] += 1
    hero.memes["humility"] += 1
    world.say(
        f"{hero.id} blinked, then laughed at {hero.pronoun('possessive')} own brag. "
        f"{hero.pronoun().capitalize()} tucked {napkin.phrase} into the lute and held the instrument close."
    )


def ignore_advice(world: World, hero: Entity, napkin: NapkinCfg) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} tossed {napkin.phrase} back onto the table. '
        f'"A napkin is for crumbs, not for my grand old lute," {hero.pronoun()} said.'
    )


def perform(world: World, hero: Entity, tune: Tune) -> None:
    sound = effective_sound(world)
    world.get("lute").meters["sound"] = float(sound)
    world.say(
        f"Then {hero.id} struck up {tune.play}. The first note leaped out so hard that cups rang and spoons tapped time."
    )
    propagate(world, narrate=False)
    if world.get("stack").meters["slid"] >= THRESHOLD:
        world.say(
            f"The music was too big for the poor dessert. {world.facts['stack_cfg'].the.capitalize()} gave one slow shiver, "
            f"and a rich layer of filling slumped down the side like a sleepy landslide."
        )
    elif world.get("stack").meters["wobble"] >= THRESHOLD:
        world.say(
            f"The table trembled and {world.facts['stack_cfg'].the} wobbled, but it held."
        )
    else:
        world.say(
            f"The notes came out warm and round, small enough to land where they were needed."
        )


def steady_finish(world: World, hero: Entity, helper: Entity, stack: Stack) -> None:
    hero.memes["joy"] += 1
    hero.memes["honesty"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"When the last string hummed quiet, {stack.the} was still standing straight. "
        f"The crowd cheered not because the tune was loud, but because it was lovely."
    )
    world.say(
        f'{hero.id} bowed and said, "I talked bigger than a thunderhead. {helper.id} was right. '
        f'A good song should help the feast, not boss it around."'
    )
    world.say(
        f"Soon slices of layer upon layer were passing from hand to hand, and the folded napkin stayed tucked in the lute like a little white badge of sense."
    )


def humble_repair(world: World, hero: Entity, helper: Entity, napkin: NapkinCfg, stack: Stack) -> None:
    world.get("napkin").meters["used"] += 1
    hero.memes["humility"] += 1
    hero.memes["honesty"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"For one hot second, {hero.id} wished the ground would open and hide {hero.pronoun('object')}. "
        f"Then {helper.id} picked up {napkin.phrase} and pressed it into {hero.pronoun('possessive')} hand."
    )
    world.say(
        f'"Use it now," {helper.pronoun()} said. "Wipe the jam, tell the truth, and play softer."'
    )
    world.say(
        f"{hero.id} cleaned the drippy edge, admitted the brag had been bigger than the tune needed to be, "
        f"and played one plain sweet verse while the cooks straightened the leaning dessert."
    )
    world.say(
        f"By supper, the feast was smaller and messier, but kinder. Even with one crooked layer, the slices tasted better after an honest apology."
    )


def tell(
    place: Place,
    tune: Tune,
    stack: Stack,
    napkin_cfg: NapkinCfg,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
    relation: str,
    hero_age: int,
    helper_age: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper_type = helper_gender
    world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        age=helper_age,
        traits=["sensible"],
        attrs={"relation": relation},
    ))
    world.add(Entity(id="lute", type="instrument", label="lute"))
    world.add(Entity(id="stack", type="dessert", label=stack.label))
    world.add(Entity(id="napkin", type="cloth", label=napkin_cfg.label))

    world.facts.update(
        place=place,
        tune=tune,
        stack_cfg=stack,
        napkin_cfg=napkin_cfg,
        using_napkin=False,
        relation=relation,
    )

    helper = world.get(helper_name)

    introduce(world, hero, helper, place, stack)
    boast(world, hero, place, tune)

    world.para()
    helper_warning(world, helper, hero, napkin_cfg, stack)

    heed = would_heed(relation, helper_age, hero_age, trait)
    world.facts["heed"] = heed

    if heed:
        accept_advice(world, hero, napkin_cfg)
    else:
        ignore_advice(world, hero, napkin_cfg)

    world.para()
    perform(world, hero, tune)

    world.para()
    if world.get("stack").meters["slid"] >= THRESHOLD:
        humble_repair(world, hero, helper, napkin_cfg, stack)
        outcome = "messy"
    else:
        steady_finish(world, hero, helper, stack)
        outcome = "steady"

    world.facts.update(
        hero=hero,
        helper=helper,
        outcome=outcome,
        stack_safe=world.get("stack").meters["slid"] < THRESHOLD,
        sound=int(world.get("lute").meters["sound"]),
        wobble=world.get("stack").meters["wobble"] >= THRESHOLD,
        slid=world.get("stack").meters["slid"] >= THRESHOLD,
    )
    return world


PLACES = {
    "fair": Place(
        id="fair",
        label="the county fair",
        image="The bunting along the booths snapped so high in the wind that children said it could tickle the moon.",
        echo=1,
        boast="the pie tins on the next hill will rattle",
        tags={"fair", "echo"},
    ),
    "mesa": Place(
        id="mesa",
        label="the red mesa feast",
        image="The flat red mesa rolled back every sound twice, as if the cliffs liked stories too much to hear them only once.",
        echo=2,
        boast="the cliffs will hum it back to us till sunset",
        tags={"mesa", "echo"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside picnic",
        image="The river lay beside the blankets, broad and shiny, carrying little whispers away but tossing big noises right back.",
        echo=1,
        boast="the fish will leap up to dance",
        tags={"river"},
    ),
}

TUNES = {
    "thunder_reel": Tune(
        id="thunder_reel",
        label="the Thunder Reel",
        brag="a tune for storms",
        play="the Thunder Reel",
        loudness=3,
        tags={"lute", "music", "loud"},
    ),
    "parade_jig": Tune(
        id="parade_jig",
        label="the Parade Jig",
        brag="a tune for marching boots",
        play="the Parade Jig",
        loudness=2,
        tags={"lute", "music"},
    ),
    "porch_hum": Tune(
        id="porch_hum",
        label="the Porch Hum",
        brag="a tune for close ears",
        play="the Porch Hum",
        loudness=1,
        tags={"lute", "music", "gentle"},
    ),
}

STACKS = {
    "layer_cake": Stack(
        id="layer_cake",
        label="layer cake",
        phrase="a berry layer cake taller than a fence post",
        image="with cream between so many layers that nobody could count them without losing track and starting over",
        steady=3,
        wobbly=True,
        tags={"layer", "cake"},
    ),
    "jam_trifle": Stack(
        id="jam_trifle",
        label="jam trifle",
        phrase="a glass jam trifle stacked almost to a small child's chin",
        image="with red fruit, yellow custard, and white cream making bright bands like sunset in a jar",
        steady=3,
        wobbly=True,
        tags={"dessert"},
    ),
    "biscuit_tower": Stack(
        id="biscuit_tower",
        label="biscuit tower",
        phrase="a biscuit tower brushed with honey",
        image="so tall that the top biscuit looked like it needed its own weather report",
        steady=4,
        wobbly=True,
        tags={"biscuit"},
    ),
    "stone_pie": Stack(
        id="stone_pie",
        label="stone pie",
        phrase="a famous stone pie baked in an iron pan",
        image="so stout and squat that it would not wobble if a mule sneezed at it",
        steady=99,
        wobbly=False,
        tags={"pie"},
    ),
}

NAPKINS = {
    "cotton": NapkinCfg(
        id="cotton",
        label="cotton napkin",
        phrase="the cotton napkin",
        muffle=2,
        sturdy=2,
        tags={"napkin", "cloth"},
    ),
    "floursack": NapkinCfg(
        id="floursack",
        label="flour-sack napkin",
        phrase="the flour-sack napkin",
        muffle=3,
        sturdy=3,
        tags={"napkin", "cloth"},
    ),
    "lace": NapkinCfg(
        id="lace",
        label="lace napkin",
        phrase="the lace napkin",
        muffle=1,
        sturdy=1,
        tags={"napkin"},
    ),
    "paper": NapkinCfg(
        id="paper",
        label="paper napkin",
        phrase="the paper napkin",
        muffle=1,
        sturdy=0,
        tags={"napkin"},
    ),
}

GIRL_NAMES = ["Mara", "Lena", "Tess", "Ivy", "Nell", "June", "Dora", "Elsie"]
BOY_NAMES = ["Beau", "Cal", "Eli", "Jude", "Wes", "Otis", "Ned", "Finn"]
TRAITS = ["humble", "careful", "steady", "showy", "boastful"]
RELATIONS = ["siblings", "cousins", "friends"]


@dataclass
class StoryParams:
    place: str = "fair"
    tune: str = "thunder_reel"
    stack: str = "layer_cake"
    napkin: str = "cotton"
    hero_name: str = "Beau"
    hero_gender: str = "boy"
    helper_name: str = "Mara"
    helper_gender: str = "girl"
    trait: str = "humble"
    relation: str = "cousins"
    hero_age: int = 7
    helper_age: int = 8
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
    "lute": [
        (
            "What is a lute?",
            "A lute is a string instrument a little like a guitar. When you pluck its strings, it makes music."
        )
    ],
    "napkin": [
        (
            "What is a napkin for?",
            "A napkin is a cloth or paper square people use to wipe fingers or protect things from little messes. In a pinch, a cloth napkin can also soften a sound or cushion something delicate."
        )
    ],
    "layer": [
        (
            "What does layer mean in food?",
            "A layer is one level resting on another level. A layer cake has several parts stacked one above the next."
        )
    ],
    "music": [
        (
            "Does louder always mean better music?",
            "No. Good music fits the place and the people listening. Sometimes a soft tune is the kindest and prettiest choice."
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility means not puffing yourself up bigger than the truth. A humble person can listen, learn, and admit a mistake."
        )
    ],
    "honesty": [
        (
            "Why is it good to admit a mistake?",
            "Admitting a mistake helps people fix the problem together. Honesty is brave because it tells the truth instead of hiding."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off something far away, like a cliff or wall, and comes back to your ears. Big open places can make sounds seem even bigger."
        )
    ],
}
KNOWLEDGE_ORDER = ["layer", "lute", "napkin", "music", "echo", "humility", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    stack = f["stack_cfg"]
    place = f["place"]
    tune = f["tune"]
    outcome = f["outcome"]
    if outcome == "steady":
        return [
            f'Write a tall tale for a 3-to-5-year-old that includes the words "layer", "lute", and "napkin", and teaches humility.',
            f"Tell a playful exaggerated story set at {place.label} where {hero.id} almost shakes {stack.the} by bragging about {tune.label}, but listens to good advice and chooses a gentler way.",
            f"Write a child-friendly moral story where loud boasting causes danger, a napkin becomes the clever fix, and the ending shows that honest, modest skill matters more than showing off.",
        ]
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the words "layer", "lute", and "napkin", and teaches humility after a mistake.',
        f"Tell an exaggerated feast-day story set at {place.label} where {hero.id} ignores a warning, plays {tune.label} too loudly, and makes {stack.the} slide before learning to tell the truth.",
        f"Write a moral tall tale in which a child boasts, a wobbly dessert suffers for it, and an honest apology helps set things right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    stack = f["stack_cfg"]
    napkin = f["napkin_cfg"]
    tune = f["tune"]
    place = f["place"]
    pred = f.get("predicted", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who brought a big lute to {place.label}, and {helper.id}, who noticed danger before the music began."
        ),
        (
            f"Why was {stack.the} in danger?",
            f"It was tall and wobbly, and {tune.label} would have come out too loudly in that echoing place. {helper.id} could tell the shaking sound might make the dessert wobble or slide."
        ),
        (
            f"What was {helper.id}'s idea with the napkin?",
            f"{helper.id} wanted to tuck {napkin.phrase} into the lute so the notes would come out softer. The napkin did not make the music ugly; it made the music gentle enough for the feast."
        ),
    ]
    if f["outcome"] == "steady":
        qa.append(
            (
                f"Why did the dessert stay safe?",
                f"It stayed safe because {hero.id} listened and used the napkin before playing. That lowered the sound from {pred.get('unsafe_sound', 0)} to {pred.get('safe_sound', 0)}, which kept the wobble from turning into a mess."
            )
        )
        qa.append(
            (
                f"What moral did {hero.id} learn?",
                f"{hero.id} learned that a person does not need to boast louder than the truth. Humility helped {hero.pronoun('object')} make music that served the feast instead of showing off."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} ignored the warning?",
                f"{hero.id} played too loudly, and {stack.the} shivered until part of it slid down the side. The mess came from bragging first and choosing care later."
            )
        )
        qa.append(
            (
                f"How did {hero.id} make things better afterward?",
                f"{hero.pronoun().capitalize()} used the napkin to help clean up and told the truth about the brag. Then {hero.pronoun()} played more softly, which turned a proud mistake into an honest ending."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"humility", "honesty", "music"}
    f = world.facts
    tags |= set(f["tune"].tags)
    tags |= set(f["napkin_cfg"].tags)
    tags |= set(f["stack_cfg"].tags)
    tags |= set(f["place"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} sound={world.facts.get('sound')} heed={world.facts.get('heed')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fair",
        tune="thunder_reel",
        stack="layer_cake",
        napkin="floursack",
        hero_name="Beau",
        hero_gender="boy",
        helper_name="June",
        helper_gender="girl",
        trait="humble",
        relation="cousins",
        hero_age=7,
        helper_age=9,
    ),
    StoryParams(
        place="mesa",
        tune="parade_jig",
        stack="jam_trifle",
        napkin="cotton",
        hero_name="Tess",
        hero_gender="girl",
        helper_name="Cal",
        helper_gender="boy",
        trait="showy",
        relation="siblings",
        hero_age=6,
        helper_age=8,
    ),
    StoryParams(
        place="riverside",
        tune="thunder_reel",
        stack="layer_cake",
        napkin="cotton",
        hero_name="Otis",
        hero_gender="boy",
        helper_name="Lena",
        helper_gender="girl",
        trait="boastful",
        relation="friends",
        hero_age=7,
        helper_age=7,
    ),
    StoryParams(
        place="mesa",
        tune="thunder_reel",
        stack="biscuit_tower",
        napkin="floursack",
        hero_name="Ivy",
        hero_gender="girl",
        helper_name="Ned",
        helper_gender="boy",
        trait="careful",
        relation="friends",
        hero_age=6,
        helper_age=6,
    ),
]


def explain_rejection(place: Place, tune: Tune, stack: Stack, napkin: NapkinCfg) -> str:
    if not stack.wobbly:
        return (
            f"(No story: {stack.the} would not wobble under a song, so there is no honest danger and no real use for a napkin fix.)"
        )
    if not hazard(place, tune, stack):
        return (
            f"(No story: {tune.label} at {place.label} is too gentle to threaten {stack.the}, so the tale has no real turn.)"
        )
    if napkin.sturdy <= 0:
        return (
            f"(No story: {napkin.phrase} is too flimsy for the lute, so it is not a reasonable fix.)"
        )
    return (
        f"(No story: {napkin.phrase} would not soften the lute enough to keep {stack.the} safe at {place.label}. Pick a sturdier or thicker napkin.)"
    )


def outcome_of(params: StoryParams) -> str:
    heed = would_heed(params.relation, params.helper_age, params.hero_age, params.trait)
    return "steady" if heed else "messy"


ASP_RULES = r"""
hazard(P,T,S) :- place(P), tune(T), stack(S), wobbly(S), echo(P,E), loudness(T,L), steady(S,St), L+E >= St.
napkin_works(P,T,S,N) :- hazard(P,T,S), napkin(N), sturdy(N,Su), Su > 0,
                         echo(P,E), loudness(T,L), steady(S,St), muffle(N,M), L+E-M < St,
                         Su >= 1 + (L+E-St).
valid(P,T,S,N) :- hazard(P,T,S), napkin_works(P,T,S,N).

older_helper :- relation(siblings), helper_age(HA), hero_age(HO), HA > HO.
older_helper :- relation(cousins), helper_age(HA), hero_age(HO), HA > HO.
heed :- trait(humble).
heed :- trait(careful).
heed :- trait(steady).
heed :- trait(showy), older_helper.

outcome(steady) :- heed.
outcome(messy) :- not heed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("echo", pid, place.echo))
    for tid, tune in TUNES.items():
        lines.append(asp.fact("tune", tid))
        lines.append(asp.fact("loudness", tid, tune.loudness))
    for sid, stack in STACKS.items():
        lines.append(asp.fact("stack", sid))
        lines.append(asp.fact("steady", sid, stack.steady))
        if stack.wobbly:
            lines.append(asp.fact("wobbly", sid))
    for nid, napkin in NAPKINS.items():
        lines.append(asp.fact("napkin", nid))
        lines.append(asp.fact("muffle", nid, napkin.muffle))
        lines.append(asp.fact("sturdy", nid, napkin.sturdy))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("hero_age", params.hero_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for seed in range(60):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale feast storyworld: a booming lute, a wobbling treat, and a napkin that teaches humility."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--stack", choices=STACKS)
    ap.add_argument("--napkin", choices=NAPKINS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.tune and args.stack and args.napkin:
        place = PLACES[args.place]
        tune = TUNES[args.tune]
        stack = STACKS[args.stack]
        napkin = NAPKINS[args.napkin]
        if (args.place, args.tune, args.stack, args.napkin) not in set(valid_combos()):
            raise StoryError(explain_rejection(place, tune, stack, napkin))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.tune is None or combo[1] == args.tune)
        and (args.stack is None or combo[2] == args.stack)
        and (args.napkin is None or combo[3] == args.napkin)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, tune_id, stack_id, napkin_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl" if rng.random() < 0.6 else hero_gender
    hero_name = _pick_name(rng, hero_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=hero_name)
    trait = args.trait or rng.choice(TRAITS)
    relation = args.relation or rng.choice(RELATIONS)
    hero_age = rng.randint(5, 8)
    helper_age = rng.randint(5, 9)
    return StoryParams(
        place=place_id,
        tune=tune_id,
        stack=stack_id,
        napkin=napkin_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tune not in TUNES:
        raise StoryError(f"(Unknown tune: {params.tune})")
    if params.stack not in STACKS:
        raise StoryError(f"(Unknown stack: {params.stack})")
    if params.napkin not in NAPKINS:
        raise StoryError(f"(Unknown napkin: {params.napkin})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.relation not in RELATIONS:
        raise StoryError(f"(Unknown relation: {params.relation})")

    combo = (params.place, params.tune, params.stack, params.napkin)
    if combo not in set(valid_combos()):
        raise StoryError(
            explain_rejection(PLACES[params.place], TUNES[params.tune], STACKS[params.stack], NAPKINS[params.napkin])
        )

    world = tell(
        place=PLACES[params.place],
        tune=TUNES[params.tune],
        stack=STACKS[params.stack],
        napkin_cfg=NAPKINS[params.napkin],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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
        print(f"{len(combos)} valid (place, tune, stack, napkin) combos:\n")
        for place, tune, stack, napkin in combos:
            print(f"  {place:10} {tune:13} {stack:14} {napkin}")
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
            header = f"### {p.hero_name} at {p.place}: {p.tune} / {p.stack} / {p.napkin} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
