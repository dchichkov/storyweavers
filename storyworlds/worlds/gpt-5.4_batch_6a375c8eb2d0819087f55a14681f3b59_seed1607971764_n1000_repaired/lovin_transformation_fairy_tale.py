#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py
=============================================================

A small fairy-tale storyworld about a child who meets an enchanted creature and
breaks the spell with a freely given, lovin gift.

The domain is intentionally narrow and constraint-checked:
- each creature has one concrete need,
- each gift helps one concrete need,
- each place only suits certain creature habitats.

A story is only valid when the place can honestly host the creature and the
chosen gift truly solves the creature's trouble. The transformation is therefore
earned by world state, not by a random magic flourish.

Run it
------
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --place riverbank --creature frog --gift bun
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --place riverbank --creature frog --gift cloak
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/lovin_transformation_fairy_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "fairy", "witch", "princess"}
        male = {"boy", "man", "father", "prince", "woodcutter"}
        neutral = {"creature", "frog", "robin", "hedgehog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)
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
    path_text: str
    light_text: str
    habitats: set[str] = field(default_factory=set)
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
class CreatureCfg:
    id: str
    label: str
    type: str
    habitat: str
    need: str
    plight: str
    sound: str
    transformed_label: str
    transformed_type: str
    true_name: str
    boon: str
    boon_image: str
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
class Gift:
    id: str
    label: str
    phrase: str
    cures: str
    carry_text: str
    give_text: str
    after_text: str
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


def _r_transform(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["helped"] < THRESHOLD or creature.meters["enchanted"] < THRESHOLD:
        return []
    sig = ("transform", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["enchanted"] = 0.0
    creature.meters["transformed"] += 1
    creature.memes["gratitude"] += 1
    world.get("hero").memes["wonder"] += 1
    return ["__transform__"]


def _r_blessing(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["transformed"] < THRESHOLD:
        return []
    sig = ("blessing", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").meters["blessing"] += 1
    world.get("hero").memes["joy"] += 1
    return ["__blessing__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform", tag="magic", apply=_r_transform),
    Rule(name="blessing", tag="magic", apply=_r_blessing),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def gift_fits(creature: CreatureCfg, gift: Gift) -> bool:
    return creature.need == gift.cures


def place_suits(place: Place, creature: CreatureCfg) -> bool:
    return creature.habitat in place.habitats


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            for gift_id, gift in GIFTS.items():
                if place_suits(place, creature) and gift_fits(creature, gift):
                    combos.append((place_id, creature_id, gift_id))
    return combos


def predict_help(world: World, creature_id: str, gift_id: str) -> dict:
    sim = world.copy()
    creature = sim.get(creature_id)
    gift = GIFTS[gift_id]
    if gift.cures == creature.attrs["need"]:
        creature.meters["need"] = 0.0
        creature.meters["helped"] += 1
    propagate(sim, narrate=False)
    return {
        "transforms": sim.get(creature_id).meters["transformed"] >= THRESHOLD,
        "need_left": sim.get(creature_id).meters["need"],
    }


def fairy_opening(world: World, hero: Entity, guide: Entity, gift: Gift) -> None:
    place = world.place
    world.say(
        f"In the days when moonlight was said to listen, {hero.id} lived in a cottage "
        f"at the edge of the kingdom. One evening {guide.label_word} sent {hero.pronoun('object')} "
        f"along {place.path_text}, and tucked {gift.phrase} into {hero.pronoun('possessive')} hands."
    )
    world.say(
        f'"Mind your steps," {guide.label_word} said, "and remember the old lovin way: '
        f'a gift given freely shines brighter than a wish begged loudly."'
    )
    world.say(place.light_text)


def set_out(world: World, hero: Entity, gift: Gift) -> None:
    hero.memes["duty"] += 1
    hero.memes["attachment"] += 1
    world.say(
        f"{hero.id} walked carefully, for {gift.carry_text}. The gift felt precious, "
        f"and for a little while {hero.pronoun()} thought only of keeping it safe."
    )


def discover_creature(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Then, near a stone where the path bent, {hero.pronoun()} heard {cfg.sound}. "
        f"There sat {cfg.plight}."
    )


def warn_of_need(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg) -> None:
    pred = predict_help(world, creature.id, world.facts["gift"].id)
    world.facts["predicted_transformation"] = pred["transforms"]
    world.say(
        f"{hero.id} knelt low and saw at once what was wrong: the little creature was "
        f"{need_phrase(cfg.need)}. A softer child might have run home, but {hero.id} stayed."
    )


def hesitate(world: World, hero: Entity, gift: Gift, cfg: CreatureCfg) -> None:
    hero.memes["conflict"] += 1
    cautious = "careful" in hero.traits or "gentle" in hero.traits
    if cautious:
        world.say(
            f"{hero.id} drew {gift.phrase} close and thought of the road ahead. If {hero.pronoun()} "
            f"shared it, there would be less for the journey."
        )
    else:
        world.say(
            f"For a heartbeat {hero.id} wanted to keep {gift.label} for the journey. "
            f"The road still seemed long, and the creature was only a stranger."
        )
    world.say(
        f"But the sight of the {cfg.label} pulled at {hero.pronoun('possessive')} heart more strongly "
        f"than any selfish thought."
    )


def give_gift(world: World, hero: Entity, creature: Entity, gift: Gift, cfg: CreatureCfg) -> None:
    hero.memes["kindness"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.meters["carried_gift"] = 0.0
    creature.attrs["gift_received"] = gift.id
    creature.owner = creature.id
    hero.attrs["gift_kept"] = False
    creature.meters["need"] = 0.0
    creature.meters["helped"] += 1
    world.say(
        f"{hero.id} did not ask for gold or luck or a grand reward. {gift.give_text}"
    )
    propagate(world, narrate=False)


def transform(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg) -> None:
    creature.type = cfg.transformed_type
    creature.label = cfg.transformed_label
    creature.attrs["true_name"] = cfg.true_name
    world.say(
        f"At once the air rang like tiny bells. The bent little shape glimmered, grew bright, "
        f"and changed into {cfg.transformed_label}."
    )
    world.say(
        f'"I am {cfg.true_name}," {creature.pronoun()} said. "Long ago I was enchanted, and only '
        f'a lovin gift freely given could loosen the spell."'
    )


def blessing(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg, gift: Gift) -> None:
    hero.attrs["boon"] = cfg.boon
    world.say(
        f"Then {creature.pronoun()} touched {hero.id}'s sleeve and {cfg.boon}."
    )
    world.say(cfg.boon_image)
    world.say(
        f"{gift.after_text}, and {hero.id} understood that kindness had turned the road itself gentler."
    )


def ending(world: World, hero: Entity, guide: Entity) -> None:
    boon = hero.attrs.get("boon", "left a quiet blessing behind")
    world.say(
        f"When {hero.id} came home, {guide.label_word} saw the light in {hero.pronoun('possessive')} face "
        f"before a single word was spoken."
    )
    world.say(
        f"From that night on, the cottage was known for {boon}, and whenever travelers passed the door, "
        f"they found it warm. So {hero.id} learned that the smallest true gift can change more than one life."
    )


def need_phrase(need: str) -> str:
    return {
        "cold": "cold and trembling",
        "hungry": "hungry and weak",
        "tangled": "caught in cruel thorns",
    }[need]


def tell(
    place: Place,
    creature_cfg: CreatureCfg,
    gift: Gift,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    guide_type: str = "grandmother",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=hero_name,
            role="hero",
            traits=list(hero_traits or ["gentle"]),
            attrs={"gift_kept": True, "boon": ""},
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_type,
            label=guide_type,
            role="guide",
            attrs={},
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="character",
            type=creature_cfg.type,
            label=creature_cfg.label,
            role="enchanted",
            owner=None,
            attrs={
                "need": creature_cfg.need,
                "true_name": creature_cfg.true_name,
                "gift_received": "",
            },
        )
    )
    hero.meters["carried_gift"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["attachment"] = 0.0
    creature.meters["need"] = 1.0
    creature.meters["enchanted"] = 1.0
    creature.meters["helped"] = 0.0
    creature.meters["transformed"] = 0.0
    creature.memes["gratitude"] = 0.0
    world.facts.update(
        hero=hero,
        guide=guide,
        creature=creature,
        creature_cfg=creature_cfg,
        gift=gift,
        place=place,
        transformed=False,
    )

    fairy_opening(world, hero, guide, gift)
    set_out(world, hero, gift)

    world.para()
    discover_creature(world, hero, creature, creature_cfg)
    warn_of_need(world, hero, creature, creature_cfg)
    hesitate(world, hero, gift, creature_cfg)

    world.para()
    give_gift(world, hero, creature, gift, creature_cfg)
    if creature.meters["transformed"] >= THRESHOLD:
        transform(world, hero, creature, creature_cfg)
        blessing(world, hero, creature, creature_cfg, gift)
    world.para()
    ending(world, hero, guide)

    world.facts["transformed"] = creature.meters["transformed"] >= THRESHOLD
    world.facts["gift_shared"] = not hero.attrs["gift_kept"]
    return world


PLACE_ORDER = ["forest_glade", "riverbank", "thorn_lane"]
PLACES = {
    "forest_glade": Place(
        id="forest_glade",
        label="the forest glade",
        path_text="the mossy forest path toward the glade",
        light_text="The last gold light of day spilled through the branches, and the leaves whispered like old ladies at a spinning wheel.",
        habitats={"forest", "sky"},
        tags={"forest"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        path_text="the willow road beside the river",
        light_text="The river wore a silver skin, and the reeds bowed whenever the wind passed over them.",
        habitats={"water", "sky"},
        tags={"river"},
    ),
    "thorn_lane": Place(
        id="thorn_lane",
        label="the thorn lane",
        path_text="the narrow lane where the hedge roses grew wild",
        light_text="Around the lane, the thorn bushes held the dusk in their branches as if they had snared bits of purple cloth.",
        habitats={"hedge", "forest"},
        tags={"hedge"},
    ),
}

CREATURES = {
    "robin": CreatureCfg(
        id="robin",
        label="a robin with puffed feathers",
        type="robin",
        habitat="sky",
        need="cold",
        plight="a robin with puffed feathers, shivering on the stone",
        sound="a thin, chirring cry",
        transformed_label="a small spring fairy in a feather-red cloak",
        transformed_type="fairy",
        true_name="Featherbright",
        boon="a trail of warm red berries sprang up each winter beneath the cottage hedge",
        boon_image="Even the frost seemed kinder after that, and bright berries shone in the snow like tiny lanterns.",
        tags={"bird", "transformation", "cold"},
    ),
    "frog": CreatureCfg(
        id="frog",
        label="a frog with dull green skin",
        type="frog",
        habitat="water",
        need="hungry",
        plight="a frog with dull green skin, too weak even to hop toward the reeds",
        sound="a faint little croak",
        transformed_label="a green-cloaked prince no taller than a chair",
        transformed_type="prince",
        true_name="Prince Reed",
        boon="the garden well never again ran dry in summer",
        boon_image="Afterward, every bucket drawn from the well came up cold and clear, even in the hottest week of the year.",
        tags={"frog", "transformation", "hunger"},
    ),
    "hedgehog": CreatureCfg(
        id="hedgehog",
        label="a hedgehog rolled tight in bramble",
        type="hedgehog",
        habitat="hedge",
        need="tangled",
        plight="a hedgehog rolled tight in bramble, with burrs and thorn-thread knotted through its prickles",
        sound="a fretful rustle",
        transformed_label="a tiny hedge-witch with a crown of leaves",
        transformed_type="witch",
        true_name="Mistress Briar",
        boon="the rose hedge around the cottage bloomed sweetly from spring until frost",
        boon_image="Soon the whole doorway smelled of roses, and bees hummed there from morning to evening.",
        tags={"hedgehog", "transformation", "thorns"},
    ),
}

GIFTS = {
    "cloak": Gift(
        id="cloak",
        label="cloak",
        phrase="a little wool cloak",
        cures="cold",
        carry_text="the wool still held the smell of lavender and hearth smoke",
        give_text="She wrapped the little wool cloak around the creature until the trembling slowed.",
        after_text="Though the cloak was no longer in her own basket, warmth seemed to walk beside her",
        tags={"cloak", "kindness", "warmth"},
    ),
    "bun": Gift(
        id="bun",
        label="bun",
        phrase="a honey bun",
        cures="hungry",
        carry_text="the bun was soft and golden, and sweet steam rose from it through the cloth",
        give_text="She broke the honey bun in gentle pieces and held them out until the creature could eat.",
        after_text="Though the bun was gone from her own hands, her hunger felt smaller than before",
        tags={"bread", "kindness", "food"},
    ),
    "comb": Gift(
        id="comb",
        label="comb",
        phrase="a silver comb",
        cures="tangled",
        carry_text="the comb flashed like a sliver of moon in the dusk",
        give_text="She sat on the stone and used the silver comb with patient fingers until every thorn and burr came free.",
        after_text="Though the comb had worked long in service of another, its silver teeth shone brighter than before",
        tags={"comb", "kindness", "grooming"},
    ),
}

GIRL_NAMES = ["Mira", "Elsa", "Nina", "Tilda", "Rose", "Lina", "Ada", "Mila"]
BOY_NAMES = ["Oren", "Tobin", "Milo", "Arlo", "Finn", "Ned", "Leo", "Bram"]
TRAITS = ["gentle", "brave", "careful", "kind", "curious"]


@dataclass
class StoryParams:
    place: str
    creature: str
    gift: str
    hero: str
    gender: str
    guide: str
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


CURATED = [
    StoryParams(
        place="forest_glade",
        creature="robin",
        gift="cloak",
        hero="Mira",
        gender="girl",
        guide="grandmother",
        trait="gentle",
    ),
    StoryParams(
        place="riverbank",
        creature="frog",
        gift="bun",
        hero="Tobin",
        gender="boy",
        guide="mother",
        trait="brave",
    ),
    StoryParams(
        place="thorn_lane",
        creature="hedgehog",
        gift="comb",
        hero="Rose",
        gender="girl",
        guide="grandmother",
        trait="careful",
    ),
    StoryParams(
        place="forest_glade",
        creature="robin",
        gift="cloak",
        hero="Bram",
        gender="boy",
        guide="father",
        trait="kind",
    ),
]


KNOWLEDGE = {
    "transformation": [
        (
            "What is a transformation in a fairy tale?",
            "A transformation is when someone changes shape because of magic. In fairy tales, the change usually reveals who they really are or what they have learned."
        )
    ],
    "kindness": [
        (
            "Why does kindness matter in many fairy tales?",
            "Kindness matters because it changes what happens next. A small good deed can open the door to help, trust, and magic."
        )
    ],
    "forest": [
        (
            "Why do fairy tales often happen in forests?",
            "Forests feel deep and mysterious, so they are good places for unexpected meetings. A child can step onto a path there and find something magical."
        )
    ],
    "river": [
        (
            "Why is a riverbank a good fairy-tale place?",
            "A riverbank feels alive because water moves, shines, and carries secrets. Fairy tales use rivers as places where change can begin."
        )
    ],
    "hedge": [
        (
            "Why are thorn hedges important in fairy tales?",
            "Thorn hedges can guard, hide, or trap things, so they make a strong symbol in fairy tales. Passing through them often means facing a hard moment bravely."
        )
    ],
    "bird": [
        (
            "Why might a bird need warmth in winter?",
            "Small birds lose heat quickly because their bodies are tiny. Warmth helps them save energy and stay alive."
        )
    ],
    "frog": [
        (
            "Why do frogs appear in fairy tales so often?",
            "Frogs can live near water and seem ordinary at first, which makes them perfect for surprise magic. A frog in a fairy tale may be more than it appears."
        )
    ],
    "thorns": [
        (
            "Why are thorns hard for small animals?",
            "Thorns can catch fur, feathers, or prickles and make it hard to move. A trapped animal may need patient help to get free."
        )
    ],
    "cloak": [
        (
            "What does a cloak do?",
            "A cloak wraps around the body and helps keep someone warm. In stories, it can also mean shelter and care."
        )
    ],
    "bread": [
        (
            "Why is sharing food a powerful gift in stories?",
            "Food helps right away because it gives comfort and strength. Sharing it shows real generosity because you give up something you could have kept."
        )
    ],
    "comb": [
        (
            "What does a comb help with?",
            "A comb helps separate knots and smooth tangled hair or fur. Used gently, it can make something hurt less and feel cared for."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "transformation",
    "kindness",
    "forest",
    "river",
    "hedge",
    "bird",
    "frog",
    "thorns",
    "cloak",
    "bread",
    "comb",
]


def explain_rejection(place: Place, creature: CreatureCfg, gift: Gift) -> str:
    if not place_suits(place, creature):
        return (
            f"(No story: {creature.label} does not belong naturally at {place.label}. "
            f"That place suits habitats {sorted(place.habitats)}, but this creature belongs to {creature.habitat}.)"
        )
    return (
        f"(No story: {gift.phrase} does not solve the creature's trouble. "
        f"The {creature.label} is {need_phrase(creature.need)}, so the gift must help with {creature.need}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature_cfg = f["creature_cfg"]
    gift = f["gift"]
    place = f["place"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "lovin" and a magical transformation.',
        f"Tell a fairy tale where a {hero.type} named {hero.id} walks through {place.label} with {gift.phrase} and meets {creature_cfg.label}.",
        f"Write a gentle transformation story where a child gives away something precious to help a creature, and the creature changes into its true form.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    creature_cfg = f["creature_cfg"]
    gift = f["gift"]
    place = f["place"]
    creature = f["creature"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who walked through {place.label} carrying {gift.phrase}. It is also about {creature_cfg.label}, whose spell was waiting to be broken."
        ),
        (
            f"Why did {hero.id} stop on the path?",
            f"{hero.id} heard {creature_cfg.sound} and found the creature in trouble. The child stopped because the creature was {need_phrase(creature_cfg.need)} and could not manage alone."
        ),
        (
            f"Why was it hard for {hero.id} to share {gift.label}?",
            f"It was hard because the gift felt precious and was meant for the journey. For a moment {hero.id} had to choose between keeping comfort and giving help."
        ),
        (
            f"How did {hero.id} help the creature?",
            help_answer(world),
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "What happened after the child helped?",
                f"The creature transformed into {creature_cfg.transformed_label}. The change happened because a lovin gift was given freely, which was exactly what the spell required."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a blessing on the home: {hero.attrs['boon']}. The last image shows that one kind act changed both the path and the cottage afterward."
            )
        )
    return qa


def help_answer(world: World) -> str:
    f = world.facts
    hero = f["hero"]
    creature_cfg = f["creature_cfg"]
    gift = f["gift"]
    if gift.id == "cloak":
        return (
            f"{hero.id} wrapped the creature in the little wool cloak until it grew warm again. That help mattered because the creature's real trouble was the cold."
        )
    if gift.id == "bun":
        return (
            f"{hero.id} shared the honey bun in small pieces until the creature had strength again. That help mattered because hunger was what held the creature low and weak."
        )
    return (
        f"{hero.id} used the silver comb patiently until the thorns and burrs came free. That help mattered because the creature was trapped by tangles, not by fear alone."
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"transformation", "kindness"}
    place = f["place"]
    creature_cfg = f["creature_cfg"]
    gift = f["gift"]
    tags |= set(place.tags)
    tags |= set(creature_cfg.tags)
    tags |= set(gift.tags)
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_gift(C, G) :- creature(C), gift(G), needs(C, N), cures(G, N).
valid(P, C, G) :- place(P), creature(C), gift(G), lives_in(C, H), affords(P, H), fits_gift(C, G).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for habitat in sorted(place.habitats):
            lines.append(asp.fact("affords", place_id, habitat))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("lives_in", creature_id, creature.habitat))
        lines.append(asp.fact("needs", creature_id, creature.need))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("cures", gift_id, gift.cures))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(7))
        sample = generate(params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: default generation smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: curated generation + emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"CURATED SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child gives a lovin gift, and an enchanted creature transforms."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["grandmother", "mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.gift:
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        gift = GIFTS[args.gift]
        if not (place_suits(place, creature) and gift_fits(creature, gift)):
            raise StoryError(explain_rejection(place, creature, gift))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    guide = args.guide or rng.choice(["grandmother", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        creature=creature_id,
        gift=gift_id,
        hero=name,
        gender=gender,
        guide=guide,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.guide not in {"grandmother", "mother", "father"}:
        raise StoryError(f"(Unknown guide: {params.guide})")

    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    gift = GIFTS[params.gift]
    if not (place_suits(place, creature) and gift_fits(creature, gift)):
        raise StoryError(explain_rejection(place, creature, gift))

    world = tell(
        place=place,
        creature_cfg=creature,
        gift=gift,
        hero_name=params.hero,
        hero_type="girl" if params.gender == "girl" else "boy",
        hero_traits=[params.trait],
        guide_type=params.guide,
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
        print(f"{len(combos)} compatible (place, creature, gift) combos:\n")
        for place_id, creature_id, gift_id in combos:
            print(f"  {place_id:12} {creature_id:10} {gift_id}")
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
            header = f"### {p.hero}: {p.creature} at {p.place} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
