#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cram_surprise_humor_animal_story.py
==============================================================

A standalone storyworld for a tiny humorous animal tale about trying to cram too
many treats into the wrong container for a surprise picnic.

The world model is simple and physical:
- a woodland animal plans a surprise treat for a friend or group,
- the hero tries to cram the treats into a too-small carrier,
- a careful helper may stop the hero before disaster,
- otherwise the overloaded carrier wobbles and spills,
- everyone still finds a better way to carry the treats, and the ending image
  proves the surprise became happier, funnier, or both.

Run it
------
python storyworlds/worlds/gpt-5.4/cram_surprise_humor_animal_story.py
python storyworlds/worlds/gpt-5.4/cram_surprise_humor_animal_story.py --qa
python storyworlds/worlds/gpt-5.4/cram_surprise_humor_animal_story.py --all
python storyworlds/worlds/gpt-5.4/cram_surprise_humor_animal_story.py --verify
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
SENSE_MIN = 2
CAREFUL_STYLES = {"careful", "steady", "practical"}


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
class Occasion:
    id: str
    reason: str
    amount: int
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
class Treat:
    id: str
    label: str
    phrase: str
    bulk: int
    plural: bool
    motion: str
    mess: str
    tags: set[str] = field(default_factory=set)

    def noun(self, amount: int) -> str:
        if self.plural:
            return f"{amount} {self.label}"
        article = "an" if self.label[:1].lower() in "aeiou" else "a"
        if amount == 1:
            return f"{article} {self.label}"
        return f"{amount} {self.label}"
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
class Container:
    id: str
    label: str
    phrase: str
    capacity: int
    stability: int
    close_sound: str
    open_sound: str
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
class PathCfg:
    id: str
    label: str
    bumpiness: int
    image: str
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
class Fix:
    id: str
    label: str
    phrase: str
    sense: int
    capacity: int
    repeatable: bool = False
    needs_helper: bool = False
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
        self.facts: dict = {
            "load": 0,
            "capacity": 0,
            "stability": 0,
            "bumpiness": 0,
            "moving": False,
            "surprise_revealed": False,
            "spill_happened": False,
            "early_help": False,
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_stuffed(world: World) -> list[str]:
    container = world.get("container")
    hero = world.get("hero")
    helper = world.get("helper")
    load = world.facts["load"]
    capacity = world.facts["capacity"]
    if load <= capacity:
        return []
    sig = ("stuffed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    container.meters["stuffed"] += float(load - capacity)
    hero.memes["determination"] += 1
    helper.memes["worry"] += 1
    return ["__stuffed__"]


def _r_wobble(world: World) -> list[str]:
    container = world.get("container")
    if container.meters["stuffed"] < THRESHOLD or not world.facts["moving"]:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    risk = (world.facts["load"] - world.facts["capacity"]) + world.facts["bumpiness"] - world.facts["stability"]
    if risk > 0:
        container.meters["wobble"] += float(risk)
    return ["__wobble__"] if risk > 0 else []


def _r_spill(world: World) -> list[str]:
    container = world.get("container")
    hero = world.get("hero")
    helper = world.get("helper")
    treats = world.get("treats")
    if container.meters["wobble"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    container.meters["spilled"] += 1
    treats.meters["scattered"] += 1
    hero.memes["embarrassment"] += 1
    helper.memes["surprise"] += 1
    world.facts["spill_happened"] = True
    return ["__spill__"]


def _r_reveal(world: World) -> list[str]:
    if not world.facts["spill_happened"]:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["surprise_revealed"] = True
    world.get("hero").memes["relief"] += 1
    world.get("helper").memes["joy"] += 1
    return ["__reveal__"]


CAUSAL_RULES = [
    Rule(name="stuffed", tag="physical", apply=_r_stuffed),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="reveal", tag="social", apply=_r_reveal),
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
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def load_units(occasion: Occasion, treat: Treat) -> int:
    return occasion.amount * treat.bulk


def risk_score(occasion: Occasion, treat: Treat, container: Container, path: PathCfg) -> int:
    return load_units(occasion, treat) - container.capacity + path.bumpiness - container.stability


def fix_works(fix: Fix, occasion: Occasion, treat: Treat) -> bool:
    need = load_units(occasion, treat)
    if fix.repeatable:
        return need > 0
    return fix.capacity >= need


def would_avert(helper_style: str) -> bool:
    return helper_style in CAREFUL_STYLES


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for occ_id, occ in OCCASIONS.items():
        for treat_id, treat in TREATS.items():
            for cont_id, cont in CONTAINERS.items():
                if load_units(occ, treat) <= cont.capacity:
                    continue
                for path_id, path in PATHS.items():
                    if risk_score(occ, treat, cont, path) <= 0:
                        continue
                    for fix_id, fix in FIXES.items():
                        if fix.sense < SENSE_MIN:
                            continue
                        if fix_works(fix, occ, treat):
                            combos.append((occ_id, treat_id, cont_id, path_id, fix_id))
    return combos


def explain_combo_rejection(occasion: Occasion, treat: Treat, container: Container, path: PathCfg, fix: Optional[Fix]) -> str:
    need = load_units(occasion, treat)
    if need <= container.capacity:
        return (
            f"(No story: {container.phrase} can already carry {treat.noun(occasion.amount)}. "
            f"If nothing must be crammed, there is no honest problem for this world.)"
        )
    if risk_score(occasion, treat, container, path) <= 0:
        return (
            f"(No story: {container.phrase} is too steady on {path.label} for the overload to matter. "
            f"This world only tells versions where cramming the treats creates a real wobble.)"
        )
    if fix is not None and fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it is known to the world but scores too low on common sense. "
            f"Choose a steadier solution like wagon, cloth_carry, or two_trips.)"
        )
    if fix is not None and not fix_works(fix, occasion, treat):
        return (
            f"(No story: {fix.phrase} would not carry enough for {occasion.reason}. "
            f"The repair must actually solve the overloaded treat problem.)"
        )
    return "(No story: this combination does not fit the world's physical logic.)"


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.facts["moving"] = True
    propagate(sim, narrate=False)
    return {
        "spill": sim.facts["spill_happened"],
        "reveal": sim.facts["surprise_revealed"],
        "risk": risk_score(
            OCCASIONS[sim.facts["occasion_id"]],
            TREATS[sim.facts["treat_id"]],
            CONTAINERS[sim.facts["container_id"]],
            PATHS[sim.facts["path_id"]],
        ),
    }


def introduce(world: World, hero: Entity, helper: Entity, occasion: Occasion) -> None:
    world.say(
        f"In a shady little forest, {hero.id} had a secret. {hero.pronoun().capitalize()} wanted to make "
        f"{occasion.reason} for {helper.id}."
    )
    world.say(
        f"{hero.id} kept smiling to {hero.pronoun('object')}self, because surprises feel even bigger in a small wood."
    )


def gather(world: World, hero: Entity, treat: Treat, occasion: Occasion, container: Container) -> None:
    amount = occasion.amount
    world.say(
        f"So {hero.id} gathered {treat.noun(amount)} and tried to tuck them into {container.phrase}."
    )
    world.say(
        f'"If I cram just one more in," {hero.id} whispered, "{helper_name}" never needs to know until the very end.'
        .replace("{helper_name}", world.get("helper").id)
    )
    world.say(
        f"The poor {container.label} answered with a tiny {container.close_sound}."
    )


def warn(world: World, helper: Entity, hero: Entity, container: Container, path: PathCfg, treat: Treat) -> None:
    pred = predict_spill(world)
    world.facts["predicted_risk"] = pred["risk"]
    if pred["spill"]:
        world.say(
            f'{helper.id} tilted {helper.pronoun("possessive")} head. "That {container.label} looks puffed up like a toad," '
            f'{helper.pronoun()} said. "If you hurry over {path.label}, the {treat.label} might {treat.motion} everywhere."'
        )
    else:
        world.say(
            f'{helper.id} peered at the bulging {container.label}. "That looks full," {helper.pronoun()} said.'
        )


def stop_and_plan(world: World, hero: Entity, helper: Entity, fix: Fix, occasion: Occasion) -> None:
    world.facts["early_help"] = True
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} laid a paw on the bulging carrier before {hero.id} could take one step."
    )
    world.say(
        f'"A surprise does not have to be squashed flat," {helper.id} said. "Let\'s use {fix.phrase} instead."'
    )
    world.say(
        f"{hero.id} blinked, then laughed. It was hard to argue with a plan that sounded much less explodey."
    )
    world.say(
        f"Together they repacked everything, and the secret stayed tucked away until {occasion.ending}."
    )


def hurry(world: World, hero: Entity, path: PathCfg) -> None:
    world.facts["moving"] = True
    hero.memes["haste"] += 1
    world.say(
        f"But {hero.id} was too eager to wait. {hero.pronoun().capitalize()} hurried along {path.label}, where {path.image}."
    )


def spill_scene(world: World, hero: Entity, helper: Entity, treat: Treat, container: Container) -> None:
    world.say(
        f"Then came a loud {container.open_sound}. The crammed load burst free, and the {treat.label} {treat.motion} in every direction."
    )
    world.say(
        f"One landed on a stump. Another slid under a fern. {helper.id} stared for one blink and then let out a surprised snort of laughter."
    )
    world.say(
        f'"Was all of this for me?" {helper.id} asked. {hero.id} tried to look dignified, but even {hero.pronoun()} had to laugh.'
    )


def repair(world: World, hero: Entity, helper: Entity, fix: Fix, treat: Treat) -> None:
    hero.memes["relief"] += 1
    helper.memes["joy"] += 1
    if fix.repeatable:
        world.say(
            f'Together they gathered the runaway {treat.label} and decided to use {fix.phrase}. '
            f'It took extra walking, but nothing else popped.'
        )
    elif fix.needs_helper:
        world.say(
            f'Together they gathered the runaway {treat.label} and used {fix.phrase}. '
            f'With two pairs of paws holding steady, the load behaved at last.'
        )
    else:
        world.say(
            f'Together they gathered the runaway {treat.label} and used {fix.phrase}. '
            f'This time the treats rode along without so much as a squeak.'
        )


def ending(world: World, hero: Entity, helper: Entity, occasion: Occasion, fix: Fix) -> None:
    hero.memes["joy"] += 1
    helper.memes["love"] += 1
    if world.facts["surprise_revealed"]:
        world.say(
            f"When they reached the picnic stump, the surprise was not secret anymore, but it was somehow better. "
            f"{occasion.ending}, and everyone agreed that the funniest parties begin with a little nonsense."
        )
    else:
        world.say(
            f"At the picnic stump, {hero.id} finally unveiled the treats. {helper.id}'s eyes grew round, "
            f"and {occasion.ending}."
        )
    world.say(
        f"{hero.id} never forgot the lesson: a good surprise can travel in {fix.label}, but it should not be crammed into the wrong thing."
    )


def tell(
    occasion: Occasion,
    treat: Treat,
    container: Container,
    path: PathCfg,
    fix: Fix,
    *,
    hero_name: str = "Pip",
    hero_species: str = "squirrel",
    helper_name: str = "Moss",
    helper_species: str = "rabbit",
    helper_style: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_species, label=hero_species, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_species, label=helper_species, role="helper"))
    carrier = world.add(Entity(id="container", kind="thing", type="container", label=container.label))
    treats_ent = world.add(Entity(id="treats", kind="thing", type=treat.id, label=treat.label))
    path_ent = world.add(Entity(id="path", kind="thing", type="path", label=path.label))
    fix_ent = world.add(Entity(id="fix", kind="thing", type="fix", label=fix.label))

    hero.attrs["style"] = "eager"
    helper.attrs["style"] = helper_style
    carrier.attrs["capacity"] = container.capacity
    carrier.attrs["stability"] = container.stability
    path_ent.attrs["bumpiness"] = path.bumpiness
    treats_ent.attrs["amount"] = occasion.amount
    treats_ent.attrs["bulk"] = treat.bulk
    fix_ent.attrs["sense"] = fix.sense

    world.facts.update(
        occasion=occasion,
        treat=treat,
        container_cfg=container,
        path_cfg=path,
        fix_cfg=fix,
        occasion_id=occasion.id,
        treat_id=treat.id,
        container_id=container.id,
        path_id=path.id,
        fix_id=fix.id,
        helper_style=helper_style,
        load=load_units(occasion, treat),
        capacity=container.capacity,
        stability=container.stability,
        bumpiness=path.bumpiness,
        moving=False,
        surprise_revealed=False,
        spill_happened=False,
        early_help=False,
    )

    introduce(world, hero, helper, occasion)
    gather(world, hero, treat, occasion, container)

    world.para()
    propagate(world, narrate=False)
    warn(world, helper, hero, container, path, treat)

    if would_avert(helper_style):
        stop_and_plan(world, hero, helper, fix, occasion)
        outcome = "averted"
    else:
        hurry(world, hero, path)
        propagate(world, narrate=False)
        world.para()
        spill_scene(world, hero, helper, treat, container)
        repair(world, hero, helper, fix, treat)
        outcome = "spilled"

    world.para()
    ending(world, hero, helper, occasion, fix)

    world.facts.update(
        hero=hero,
        helper=helper,
        treats_entity=treats_ent,
        container_entity=carrier,
        path_entity=path_ent,
        fix_entity=fix_ent,
        outcome=outcome,
        load_units=load_units(occasion, treat),
        risk=risk_score(occasion, treat, container, path),
    )
    return world


OCCASIONS = {
    "birthday": Occasion(
        id="birthday",
        reason="a birthday nibble-feast",
        amount=4,
        ending="the whole stump rang with happy chewing and silly birthday songs",
        tags={"party", "surprise"},
    ),
    "rain_cheer": Occasion(
        id="rain_cheer",
        reason="a rainy-day cheer-up snack",
        amount=5,
        ending="the gray afternoon suddenly felt bright and snappy again",
        tags={"rain", "surprise"},
    ),
    "welcome_home": Occasion(
        id="welcome_home",
        reason="a welcome-home forest picnic",
        amount=4,
        ending="the clearing filled with smiles, crumbs, and a warm welcome-home cheer",
        tags={"welcome", "surprise"},
    ),
}

TREATS = {
    "apples": Treat(
        id="apples",
        label="apples",
        phrase="shiny little apples",
        bulk=2,
        plural=True,
        motion="rolled",
        mess="thumped in the moss",
        tags={"apple", "food"},
    ),
    "muffins": Treat(
        id="muffins",
        label="berry muffins",
        phrase="berry muffins",
        bulk=2,
        plural=True,
        motion="bounced",
        mess="sprinkled crumbs",
        tags={"muffin", "food"},
    ),
    "nuts": Treat(
        id="nuts",
        label="nuts",
        phrase="a pile of polished nuts",
        bulk=1,
        plural=True,
        motion="pinged",
        mess="skittered through leaves",
        tags={"nut", "food"},
    ),
    "melon": Treat(
        id="melon",
        label="melon",
        phrase="a round melon",
        bulk=6,
        plural=False,
        motion="lurched",
        mess="wobbled in the dirt",
        tags={"melon", "food"},
    ),
}

CONTAINERS = {
    "pockets": Container(
        id="pockets",
        label="pockets",
        phrase="a little apron with two pockets",
        capacity=3,
        stability=1,
        close_sound="eep",
        open_sound="pop",
        tags={"pocket"},
    ),
    "leaf_basket": Container(
        id="leaf_basket",
        label="leaf basket",
        phrase="a leaf basket woven from reeds",
        capacity=5,
        stability=2,
        close_sound="creak",
        open_sound="boing",
        tags={"basket"},
    ),
    "teacup_tray": Container(
        id="teacup_tray",
        label="teacup tray",
        phrase="a tiny teacup tray",
        capacity=2,
        stability=1,
        close_sound="clink",
        open_sound="plink",
        tags={"tray"},
    ),
}

PATHS = {
    "root_path": PathCfg(
        id="root_path",
        label="the rooty path",
        bumpiness=2,
        image="tree roots made little ribs across the ground",
        tags={"path"},
    ),
    "bridge": PathCfg(
        id="bridge",
        label="the old bridge",
        bumpiness=3,
        image="the planks gave a mischievous bob with every step",
        tags={"bridge"},
    ),
    "pebble_lane": PathCfg(
        id="pebble_lane",
        label="the pebble lane",
        bumpiness=1,
        image="small stones clicked under busy feet",
        tags={"path"},
    ),
}

FIXES = {
    "wagon": Fix(
        id="wagon",
        label="a red wagon",
        phrase="a red wagon",
        sense=3,
        capacity=12,
        repeatable=False,
        needs_helper=False,
        tags={"wagon"},
    ),
    "cloth_carry": Fix(
        id="cloth_carry",
        label="a knotted picnic cloth",
        phrase="a knotted picnic cloth between them",
        sense=3,
        capacity=10,
        repeatable=False,
        needs_helper=True,
        tags={"cloth"},
    ),
    "two_trips": Fix(
        id="two_trips",
        label="two calm trips",
        phrase="two calm trips",
        sense=2,
        capacity=0,
        repeatable=True,
        needs_helper=False,
        tags={"patience"},
    ),
    "tail_stack": Fix(
        id="tail_stack",
        label="a tail-stack trick",
        phrase="a silly tail-stack trick",
        sense=1,
        capacity=1,
        repeatable=False,
        needs_helper=False,
        tags={"silly"},
    ),
}

HEROES = [
    ("Pip", "squirrel"),
    ("Tumble", "hedgehog"),
    ("Bramble", "beaver"),
    ("Nip", "chipmunk"),
]
HELPERS = [
    ("Moss", "rabbit"),
    ("Wren", "fox"),
    ("Clover", "otter"),
    ("Fern", "badger"),
]
HELPER_STYLES = ["careful", "steady", "practical", "giggly", "bouncy", "distracted"]


@dataclass
class StoryParams:
    occasion: str
    treat: str
    container: str
    path: str
    fix: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    helper_style: str
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
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something kind or exciting that someone keeps secret until the right moment. The fun comes from not knowing it is coming.",
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon carries things that are too bulky to hold in your paws. Its wheels help move a load more steadily.",
        )
    ],
    "cloth": [
        (
            "How can a cloth help carry food?",
            "If you spread a cloth flat and tie the corners, it can hold a small pile of things together. Two friends can carry it more steadily than one overstuffed pocket.",
        )
    ],
    "patience": [
        (
            "Why can two trips be smarter than one overloaded trip?",
            "Two trips may take longer, but each trip is lighter and steadier. Going a little slower can stop a big mess.",
        )
    ],
    "apple": [
        (
            "Why do apples roll away so easily?",
            "Apples are round, so they keep moving when the ground tips or bumps them. That is why a rolling apple can be hard to catch.",
        )
    ],
    "muffin": [
        (
            "What happens when a muffin bounces?",
            "A muffin may bounce a little and shed crumbs. Soft food can still make a funny mess when it lands.",
        )
    ],
    "nut": [
        (
            "Why do nuts skitter on the ground?",
            "Small hard nuts are smooth and quick. When they spill, they can ping and skitter between leaves and stones.",
        )
    ],
    "melon": [
        (
            "Why is a melon hard to cram into a tiny container?",
            "A melon is large and round, so it takes up a lot of room. If the container is too small, the load becomes awkward and unstable.",
        )
    ],
}
KNOWLEDGE_ORDER = ["surprise", "apple", "muffin", "nut", "melon", "wagon", "cloth", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    occasion = f["occasion"]
    treat = f["treat"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny animal story for a 3-to-5-year-old that includes the word "cram" and ends with a secret surprise still intact.',
            f"Tell a gentle woodland story where {hero.id} tries to cram {treat.label} into the wrong container for {occasion.reason}, but {helper.id} stops the trouble before anything spills.",
            f"Write an animal story with humor and a happy surprise where a careful friend suggests a better way to carry treats.",
        ]
    return [
        f'Write a funny animal story for a 3-to-5-year-old that includes the word "cram" and features a surprise picnic.',
        f"Tell a woodland story where {hero.id} tries to cram too many {treat.label} into a small container, the load bursts open, and the secret surprise is revealed in a silly way.",
        f"Write an animal story with humor and surprise where spilled treats lead to laughter instead of a ruined day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    occasion = f["occasion"]
    treat = f["treat"]
    container = f["container_cfg"]
    path = f["path_cfg"]
    fix = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {helper.id} the {helper.type}. {hero.id} wanted to prepare {occasion.reason}.",
        ),
        (
            f"Why did {hero.id} try to cram the treats into {container.phrase}?",
            f"{hero.id} wanted to carry everything at once and keep the treat plan a surprise. That is why {hero.pronoun()} squeezed too much into a carrier that was not big enough.",
        ),
        (
            f"Why was the container a bad choice?",
            f"The load was bigger than {container.phrase} could hold, and the path was bumpy too. That made the carrier risky before the trip even started.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did {helper.id} stop the problem?",
                f"{helper.id} noticed the bulging load and stopped {hero.id} before {hero.pronoun()} set off. Then {helper.pronoun()} suggested {fix.phrase}, which gave the treats a steadier way to travel.",
            )
        )
        qa.append(
            (
                "Was the surprise spoiled?",
                f"No. The treats were repacked before anything burst open, so the secret lasted until the picnic stump. The ending shows that a calmer plan protected the surprise.",
            )
        )
    else:
        qa.append(
            (
                f"What happened on {path.label}?",
                f"The overloaded carrier burst open and the {treat.label} {treat.motion} everywhere. The spill revealed that {hero.id} had been planning a surprise treat all along.",
            )
        )
        qa.append(
            (
                f"How did they fix the mess?",
                f"They gathered the scattered treats and switched to {fix.phrase}. The better carrier solved the real problem because the first one had been too cramped and shaky.",
            )
        )
        qa.append(
            (
                "Why is the ending funny instead of sad?",
                f"The spill was silly, and once the secret was out, everyone laughed instead of fighting. The surprise changed shape, but it still became a happy picnic.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"surprise"}
    tags |= set(world.facts["treat"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k not in {'hero', 'helper', 'occasion', 'treat', 'container_cfg', 'path_cfg', 'fix_cfg', 'treats_entity', 'container_entity', 'path_entity', 'fix_entity'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        occasion="birthday",
        treat="apples",
        container="pockets",
        path="bridge",
        fix="wagon",
        hero_name="Pip",
        hero_species="squirrel",
        helper_name="Moss",
        helper_species="rabbit",
        helper_style="giggly",
    ),
    StoryParams(
        occasion="rain_cheer",
        treat="muffins",
        container="leaf_basket",
        path="bridge",
        fix="cloth_carry",
        hero_name="Tumble",
        hero_species="hedgehog",
        helper_name="Clover",
        helper_species="otter",
        helper_style="careful",
    ),
    StoryParams(
        occasion="welcome_home",
        treat="nuts",
        container="teacup_tray",
        path="root_path",
        fix="two_trips",
        hero_name="Nip",
        hero_species="chipmunk",
        helper_name="Fern",
        helper_species="badger",
        helper_style="bouncy",
    ),
    StoryParams(
        occasion="birthday",
        treat="melon",
        container="teacup_tray",
        path="bridge",
        fix="wagon",
        hero_name="Bramble",
        hero_species="beaver",
        helper_name="Wren",
        helper_species="fox",
        helper_style="practical",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.helper_style):
        return "averted"
    return "spilled"


ASP_RULES = r"""
load(O,T,L) :- need(O,N), bulk(T,B), L = N * B.
overload(O,T,C,D) :- load(O,T,L), capacity(C,Cap), D = L - Cap, D > 0.
risky(O,T,C,P) :- overload(O,T,C,D), bumpiness(P,B), stability(C,S), D + B > S.

solves(F,O,T) :- fix(F), repeatable(F), load(O,T,_).
solves(F,O,T) :- fix(F), not repeatable(F), load(O,T,L), fix_capacity(F,C), C >= L.

valid(O,T,C,P,F) :- occasion(O), treat(T), container(C), path(P), fix(F),
                    risky(O,T,C,P), sensible(F), solves(F,O,T).

early_help :- helper_style(H), careful_style(H).
outcome(averted) :- early_help.
outcome(spilled) :- not early_help, chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, occ in OCCASIONS.items():
        lines.append(asp.fact("occasion", oid))
        lines.append(asp.fact("need", oid, occ.amount))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("bulk", tid, treat.bulk))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("capacity", cid, container.capacity))
        lines.append(asp.fact("stability", cid, container.stability))
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("bumpiness", pid, path.bumpiness))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("fix_capacity", fid, fix.capacity))
        if fix.repeatable:
            lines.append(asp.fact("repeatable", fid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for style in sorted(CAREFUL_STYLES):
        lines.append(asp.fact("careful_style", style))
    lines.append("sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_valid"),
            asp.fact("helper_style", params.helper_style),
            asp.fact("chosen_occasion", params.occasion),
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_fix", params.fix),
        ]
    )
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
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - defensive verify mode
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Humorous animal storyworld: a woodland animal tries to cram a surprise treat into the wrong carrier."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper-style", choices=HELPER_STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix is not None and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_combo_rejection(
            OCCASIONS[args.occasion] if args.occasion else next(iter(OCCASIONS.values())),
            TREATS[args.treat] if args.treat else next(iter(TREATS.values())),
            CONTAINERS[args.container] if args.container else next(iter(CONTAINERS.values())),
            PATHS[args.path] if args.path else next(iter(PATHS.values())),
            FIXES[args.fix],
        ))

    if args.occasion and args.treat and args.container and args.path:
        fix = FIXES[args.fix] if args.fix else None
        combo_ok = load_units(OCCASIONS[args.occasion], TREATS[args.treat]) > CONTAINERS[args.container].capacity
        combo_ok = combo_ok and risk_score(
            OCCASIONS[args.occasion],
            TREATS[args.treat],
            CONTAINERS[args.container],
            PATHS[args.path],
        ) > 0
        if not combo_ok or (fix is not None and not fix_works(fix, OCCASIONS[args.occasion], TREATS[args.treat])):
            raise StoryError(explain_combo_rejection(
                OCCASIONS[args.occasion],
                TREATS[args.treat],
                CONTAINERS[args.container],
                PATHS[args.path],
                fix,
            ))

    combos = [
        combo for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.treat is None or combo[1] == args.treat)
        and (args.container is None or combo[2] == args.container)
        and (args.path is None or combo[3] == args.path)
        and (args.fix is None or combo[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion, treat, container, path, fix = rng.choice(sorted(combos))
    hero_name, hero_species = rng.choice(HEROES)
    helper_name, helper_species = rng.choice([h for h in HELPERS if h[0] != hero_name])
    helper_style = args.helper_style or rng.choice(HELPER_STYLES)
    return StoryParams(
        occasion=occasion,
        treat=treat,
        container=container,
        path=path,
        fix=fix,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        helper_style=helper_style,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        occasion = OCCASIONS[params.occasion]
        treat = TREATS[params.treat]
        container = CONTAINERS[params.container]
        path = PATHS[params.path]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if (params.occasion, params.treat, params.container, params.path, params.fix) not in set(valid_combos()):
        raise StoryError(
            explain_combo_rejection(occasion, treat, container, path, fix)
        )

    world = tell(
        occasion,
        treat,
        container,
        path,
        fix,
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        helper_name=params.helper_name,
        helper_species=params.helper_species,
        helper_style=params.helper_style,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (occasion, treat, container, path, fix) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} the {p.hero_species}: {p.treat} in {p.container} ({p.path}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
