#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py
=======================================================================================

A standalone storyworld for a fairy-tale-shaped kindness story:

A child is hurrying through a castle chamber to sell small wares at the morning
fair. There the child notices someone in urgent, embarrassed trouble: they need
the privy, their bladder hurts, and one practical obstacle stands in the way.
Instead of hurrying on, the child stops to help with a matching, sensible aid.
That act of kindness pays back in a happy ending, and the opening scene plants
little foreshadowing clues that the stranger is more than they first seem.

The reasonableness gate is simple and child-facing:
a story is only valid when the chosen chamber can honestly host the obstacle,
and the chosen aid truly solves that obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py --all
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py --qa
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py --asp
    python storyworlds/worlds/gpt-5.4/bladder_chamber_sell_happy_ending_foreshadowing_kindness.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "princess"}
        male = {"boy", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandmother"}.get(
            self.type, self.type
        )
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
class Chamber:
    id: str
    label: str
    phrase: str
    detail: str
    fair_path: str
    affords: set[str] = field(default_factory=set)
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
class Goods:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Visitor:
    id: str
    label: str
    type: str
    arrival: str
    sign: str
    bladder_line: str
    foreshadow: str
    reveal: str
    reward: str
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
    need: str
    place_detail: str
    delay_text: str
    solved_text: str
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
class Aid:
    id: str
    label: str
    kind: str
    act: str
    success_text: str
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


class World:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
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
        clone = World(self.chamber)
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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if visitor.meters["urgency"] < THRESHOLD or visitor.meters["access"] >= THRESHOLD:
        return out
    sig = ("distress", visitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.memes["embarrassment"] += 1
    visitor.memes["fear"] += 1
    out.append("__distress__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    visitor = world.get("visitor")
    if hero.memes["kindness"] < THRESHOLD or visitor.memes["fear"] < THRESHOLD:
        return out
    sig = ("trust", hero.id, visitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.memes["trust"] += 1
    out.append("__trust__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if visitor.meters["access"] < THRESHOLD or visitor.meters["urgency"] < THRESHOLD:
        return out
    sig = ("relief", visitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.meters["urgency"] = 0.0
    visitor.memes["relief"] += 1
    visitor.memes["embarrassment"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="kindness", tag="social", apply=_r_kindness),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def obstacle_fits(chamber: Chamber, obstacle: Obstacle) -> bool:
    return obstacle.id in chamber.affords


def aid_fits(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.need == aid.kind


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for chamber_id, chamber in CHAMBERS.items():
        for visitor_id in VISITORS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for aid_id, aid in AIDS.items():
                    if obstacle_fits(chamber, obstacle) and aid_fits(obstacle, aid):
                        combos.append((chamber_id, visitor_id, obstacle_id, aid_id))
    return combos


def predict_relief(world: World, aid: Aid) -> bool:
    sim = world.copy()
    visitor = sim.get("visitor")
    if aid.kind == sim.facts["obstacle"].need:
        visitor.meters["access"] += 1
    propagate(sim, narrate=False)
    return visitor.memes["relief"] >= THRESHOLD


def introduce(world: World, hero: Entity, guardian: Entity, goods: Goods, chamber: Chamber) -> None:
    world.say(
        f"Once, in the bright days when bells could sound like birds, {hero.id} lived with "
        f"{hero.pronoun('possessive')} {guardian.label_word} beside the castle hill."
    )
    world.say(
        f"That morning {hero.pronoun()} carried {goods.phrase} and hoped to sell {goods.it()} "
        f"at the fair. The path to the market wound through {chamber.phrase}."
    )
    world.say(chamber.detail)


def meet_need(world: World, hero: Entity, visitor: Entity, obstacle: Obstacle, chamber: Chamber) -> None:
    visitor.meters["urgency"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"In that {chamber.label}, {visitor.arrival}. {visitor.sign}"
    )
    world.say(
        f'"Please," {visitor.pronoun()} whispered, "{visitor.attrs["need_line"]}"'
    )
    world.say(
        f"{obstacle.place_detail} {obstacle.delay_text}"
    )


def choose_kindness(world: World, hero: Entity, goods: Goods, visitor: Entity) -> None:
    hero.memes["kindness"] = 1.0
    hero.memes["tempted_to_hurry"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} heard the market bell far away and knew that hurrying on might help "
        f"{hero.pronoun('object')} sell {goods.it()} before noon."
    )
    world.say(
        f"But kindness tugged harder than hurry. {hero.pronoun().capitalize()} set {goods.it()} "
        f"carefully on a bench and stayed."
    )


def help_with_aid(world: World, hero: Entity, visitor: Entity, aid: Aid, obstacle: Obstacle) -> None:
    if not predict_relief(world, aid):
        raise StoryError("The chosen aid does not truly solve the problem in this world.")
    visitor.meters["access"] += 1
    visitor.attrs["aid_used"] = aid.id
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} spoke softly and {aid.act}. "{aid.success_text}"'
    )
    world.say(
        obstacle.solved_text
    )
    world.say(
        f"Soon the poor traveler hurried away, and when {visitor.pronoun()} came back, "
        f"{visitor.pronoun('possessive')} face looked peaceful instead of pinched."
    )


def reveal_reward(world: World, hero: Entity, visitor: Entity, goods: Goods, chamber: Chamber) -> None:
    hero.memes["wonder"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Then the little clue from before made sense: {visitor.attrs['foreshadow']}"
    )
    world.say(
        visitor.reveal
    )
    world.say(
        visitor.reward.format(
            hero=hero.id,
            goods=goods.label,
            chamber=chamber.label,
        )
    )
    world.say(
        f"So {hero.id} did sell every bit of {goods.label} after all, and went home with light feet, "
        f"a warm heart, and a story that sounded almost like magic."
    )


def closing_image(world: World, hero: Entity, guardian: Entity, goods: Goods) -> None:
    world.say(
        f"That evening {guardian.label_word} counted the fair coins, but {hero.id} smiled most at something else."
    )
    world.say(
        f"In the fairy-tale hush after supper, {hero.pronoun()} remembered how one kind pause had turned a stranger's pain into relief. "
        f"From then on, whenever {hero.pronoun()} went out to sell {goods.label}, {hero.pronoun()} looked first for who might need help."
    )


def tell(
    chamber: Chamber,
    goods: Goods,
    visitor_cfg: Visitor,
    obstacle: Obstacle,
    aid: Aid,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    guardian_type: str = "grandmother",
) -> World:
    world = World(chamber)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    guardian = world.add(
        Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the guardian")
    )
    visitor = world.add(
        Entity(
            id="visitor",
            kind="character",
            type=visitor_cfg.type,
            role="visitor",
            label=visitor_cfg.label,
            attrs={"need_line": visitor_cfg.bladder_line, "foreshadow": visitor_cfg.foreshadow},
        )
    )
    goods_ent = world.add(
        Entity(id="goods", type="goods", label=goods.label, attrs={"goods_id": goods.id})
    )

    introduce(world, hero, guardian, goods, chamber)

    world.para()
    meet_need(world, hero, visitor, obstacle, chamber)
    choose_kindness(world, hero, goods, visitor)

    world.para()
    help_with_aid(world, hero, visitor, aid, obstacle)

    world.para()
    reveal_reward(world, hero, visitor, goods, chamber)
    closing_image(world, hero, guardian, goods)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        visitor=visitor,
        goods=goods,
        goods_entity=goods_ent,
        chamber=chamber,
        obstacle=obstacle,
        aid=aid,
        solved=visitor.memes["relief"] >= THRESHOLD,
        had_distress=True,
        foreshadow=visitor_cfg.foreshadow,
        reveal=visitor_cfg.reveal,
    )
    return world


CHAMBERS = {
    "moon": Chamber(
        id="moon",
        label="Moon Chamber",
        phrase="the Moon Chamber",
        detail="Its high windows poured silver stripes over the floor, and a narrow stair curled away behind a carved screen.",
        fair_path="past the moon windows",
        affords={"dark_stair", "shy_crowd"},
        tags={"castle", "chamber"},
    ),
    "tapestry": Chamber(
        id="tapestry",
        label="Tapestry Chamber",
        phrase="the Tapestry Chamber",
        detail="Great woven lions watched from the walls, and people waiting for market permits whispered along the benches.",
        fair_path="through the long hall of woven lions",
        affords={"shy_crowd", "locked_door"},
        tags={"castle", "chamber"},
    ),
    "clock": Chamber(
        id="clock",
        label="Clock Chamber",
        phrase="the Clock Chamber",
        detail="Tiny brass birds clicked above the hourglass shelf, and an old oak door stood near the privy passage.",
        fair_path="under the ticking rafters",
        affords={"locked_door", "dark_stair"},
        tags={"castle", "chamber"},
    ),
}

GOODS = {
    "cakes": Goods(
        id="cakes",
        label="honey cakes",
        phrase="a basket of honey cakes",
        plural=True,
        tags={"market", "cakes", "sell"},
    ),
    "ribbons": Goods(
        id="ribbons",
        label="blue ribbons",
        phrase="a loop of blue ribbons",
        plural=True,
        tags={"market", "ribbons", "sell"},
    ),
    "pears": Goods(
        id="pears",
        label="golden pears",
        phrase="a sack of golden pears",
        plural=True,
        tags={"market", "pears", "sell"},
    ),
}

VISITORS = {
    "page": Visitor(
        id="page",
        label="a mouse page in a velvet cap",
        type="boy",
        arrival="a mouse page in a velvet cap was hopping from one slipper to the other",
        sign="He kept squeezing his knees together, and a little silver seal glimmered on his cap.",
        bladder_line="my bladder hurts, and I must reach the privy at once",
        foreshadow="the silver seal on the cap had been the queen's own moon mark",
        reveal="The mouse page bowed low and admitted that he carried messages for the queen herself.",
        reward="{hero} was led to the best stall in the market, where palace cooks bought all the {goods} before the sun reached the middle of the sky.",
        tags={"mouse", "queen", "kindness"},
    ),
    "duck": Visitor(
        id="duck",
        label="a duckling messenger in a green cloak",
        type="girl",
        arrival="a duckling messenger in a green cloak was doing a tiny, worried dance",
        sign="She held her satchel under one wing, and a golden thread shone in its seam.",
        bladder_line="my bladder is so full, and I cannot bear to have an accident in the castle",
        foreshadow="the golden thread belonged to the royal post",
        reveal="The duckling laughed with relief and said she was the swiftest messenger in the royal post.",
        reward="With a clap of her wings she called the market crier, who sang of {hero}'s fine {goods}, and people hurried over until not one piece was left to sell.",
        tags={"duck", "message", "kindness"},
    ),
    "dragon": Visitor(
        id="dragon",
        label="a young dragon with a hood over his horns",
        type="boy",
        arrival="a young dragon with a hood over his horns stood very still, trying not to squirm",
        sign="Now and then a spark popped from his nose, and ruby thread glittered in the edge of his hood.",
        bladder_line="my poor bladder aches, but I do not know this part of the castle",
        foreshadow="the ruby thread was stitched in the pattern worn only by the king's household",
        reveal="The hood slipped back, and the shy traveler turned out to be one of the king's own dragon pages.",
        reward="He thanked {hero} and sent a trumpet boy ahead, so when {hero} reached the market a smiling crowd was already waiting to buy the {goods}.",
        tags={"dragon", "royal", "kindness"},
    ),
}

OBSTACLES = {
    "dark_stair": Obstacle(
        id="dark_stair",
        label="dark stair",
        need="light",
        place_detail="The privy lay down a dim little stair where shadows pooled under every step.",
        delay_text="No wonder the traveler had not dared rush into the dark alone.",
        solved_text="With a safe glow to follow, the way no longer looked frightening at all.",
        tags={"dark", "light"},
    ),
    "locked_door": Obstacle(
        id="locked_door",
        label="locked door",
        need="key",
        place_detail="The nearest privy door was shut fast, and its old brass lock had caught again.",
        delay_text="The traveler had found the right place, but could not get inside.",
        solved_text="The stubborn lock clicked open at once, and the whole trouble became simple.",
        tags={"door", "key"},
    ),
    "shy_crowd": Obstacle(
        id="shy_crowd",
        label="shy crowd",
        need="privacy",
        place_detail="The way to the privy passed a bench full of staring strangers, and the traveler was too shy to ask them to move.",
        delay_text="Embarrassment can feel as heavy as any locked gate.",
        solved_text="With a little shelter and a gentle word, the path felt private enough to cross.",
        tags={"shy", "privacy"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="blue lantern",
        kind="light",
        act="lifted a blue lantern from the wall and held it low before the steps",
        success_text="Here is light enough for brave feet.",
        qa_text="used a blue lantern to light the dark stair",
        tags={"light", "lantern"},
    ),
    "sunjar": Aid(
        id="sunjar",
        label="sun jar",
        kind="light",
        act="uncorked a tiny sun jar from the window ledge, and soft gold shone out",
        success_text="Even a small light can chase a big shadow away.",
        qa_text="opened a sun jar so the dark stair glowed softly",
        tags={"light", "jar"},
    ),
    "brass_key": Aid(
        id="brass_key",
        label="brass key",
        kind="key",
        act="borrowed the brass key hanging by the steward's board and turned it in the lock",
        success_text="Old doors remember kindness when hands stay gentle.",
        qa_text="used the brass key to open the stuck privy door",
        tags={"key", "door"},
    ),
    "oil_drop": Aid(
        id="oil_drop",
        label="drop of lamp oil",
        kind="key",
        act="tipped one careful drop of lamp oil into the old lock and worked the latch until it moved",
        success_text="There now, old lock, wake up and mind your manners.",
        qa_text="freed the old lock with a careful drop of oil",
        tags={"key", "door"},
    ),
    "screen": Aid(
        id="screen",
        label="folding screen",
        kind="privacy",
        act="pulled a folding screen across the staring bench and stood beside it like a faithful guard",
        success_text="Go on. No one here will tease you while I am watching.",
        qa_text="moved a folding screen to make a private path",
        tags={"privacy", "screen"},
    ),
    "cloak": Aid(
        id="cloak",
        label="patched blue cloak",
        kind="privacy",
        act="opened {hero_pos} patched blue cloak wide between the benches and the passage",
        success_text="You may pass behind this and keep your dignity too.",
        qa_text="used a cloak to give the traveler a private path",
        tags={"privacy", "cloak"},
    ),
}

GIRL_NAMES = ["Mira", "Elsie", "Nella", "Poppy", "Tilda", "Wren"]
BOY_NAMES = ["Rowan", "Tobin", "Milo", "Finn", "Pip", "Alden"]
TRAITS = ["kind", "gentle", "quick-eyed", "patient", "cheerful"]
GUARDIANS = ["grandmother", "mother", "father"]


@dataclass
class StoryParams:
    chamber: str
    goods: str
    visitor: str
    obstacle: str
    aid: str
    hero_name: str
    hero_type: str
    guardian_type: str
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


KNOWLEDGE = {
    "castle": [
        (
            "What is a chamber in a castle?",
            "A chamber is a room inside a castle or a big old house. Some chambers are grand, and some are plain, but they are all just rooms people use."
        )
    ],
    "bladder": [
        (
            "What does it mean if someone's bladder is too full?",
            "A bladder is the part of the body that holds pee until it is time to use the toilet or privy. If it gets too full, the person feels a strong need to go right away."
        )
    ],
    "privy": [
        (
            "What is a privy?",
            "A privy is an old-fashioned word for a toilet or bathroom. In fairy tales, castles and cottages often have privies instead of modern bathrooms."
        )
    ],
    "market": [
        (
            "What does sell mean?",
            "To sell something means to offer it to other people in return for money or coins. At a market, people sell food, cloth, toys, and many other things."
        )
    ],
    "light": [
        (
            "Why does a light help in a dark stair?",
            "A light helps you see the steps, the walls, and where to put your feet. That makes the dark place feel safer and easier to cross."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key turns inside a lock so a door can open or close. When the right key fits, a stuck door can stop being a problem."
        )
    ],
    "privacy": [
        (
            "What is privacy?",
            "Privacy means having a little space where people are not staring at you. It can help someone feel calm and safe when they are embarrassed."
        )
    ],
    "kindness": [
        (
            "Why can kindness change a whole day?",
            "Kindness can turn fear into relief because it shows someone they are not alone. A small helpful act can solve a big worry."
        )
    ],
}
KNOWLEDGE_ORDER = ["castle", "bladder", "privy", "market", "light", "key", "privacy", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    chamber = f["chamber"]
    goods = f["goods"]
    visitor = f["visitor"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "bladder", "chamber", and "sell".',
        f"Tell a gentle castle story where {hero.id} is on the way to sell {goods.label}, but stops in the {chamber.label} to help {visitor.label} with a {obstacle.label}.",
        f"Write a kind fairy tale with foreshadowing, where a child uses {aid.label} to help an embarrassed traveler and is repaid with a happy ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    visitor = f["visitor"]
    goods = f["goods"]
    chamber = f["chamber"]
    obstacle = f["obstacle"]
    aid = f["aid"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was walking through the {chamber.label} to sell {goods.label}, and a worried traveler who needed help. The story also includes {hero.pronoun('possessive')} {guardian.label_word}, waiting at home for news of the fair."
        ),
        (
            f"Why did {hero.id} stop in the {chamber.label}?",
            f"{hero.id} noticed that the traveler was in pain and too upset to manage alone. The traveler said {visitor.pronoun('possessive')} bladder hurt, so kindness mattered more than hurrying to the market."
        ),
        (
            f"What problem was in the way of the privy?",
            f"The trouble was {obstacle.label}. That obstacle kept a simple need from being easy, which is why the visitor grew embarrassed and afraid."
        ),
        (
            f"How did {hero.id} help?",
            f"{hero.id} {aid.qa_text}. That worked because the aid matched the real problem instead of only looking busy."
        ),
        (
            "What was the foreshadowing clue?",
            f"The clue was this: {f['foreshadow']}. At first it seemed like a small shiny detail, but later it showed that the traveler belonged to the royal household."
        ),
        (
            "How did the story end?",
            f"It ended happily because the traveler repaid the kindness and helped {hero.id} sell all the {goods.label}. The ending image proves what changed: one kind pause in a castle chamber turned worry into relief and luck into joy."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"castle", "bladder", "privy", "market", "kindness"}
    obstacle = world.facts["obstacle"]
    aid = world.facts["aid"]
    if obstacle.need == "light":
        tags.add("light")
    if obstacle.need == "key":
        tags.add("key")
    if obstacle.need == "privacy":
        tags.add("privacy")
    if "privacy" in aid.tags:
        tags.add("privacy")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        chamber="moon",
        goods="cakes",
        visitor="page",
        obstacle="dark_stair",
        aid="lantern",
        hero_name="Mira",
        hero_type="girl",
        guardian_type="grandmother",
        trait="kind",
        seed=1,
    ),
    StoryParams(
        chamber="tapestry",
        goods="ribbons",
        visitor="duck",
        obstacle="shy_crowd",
        aid="screen",
        hero_name="Rowan",
        hero_type="boy",
        guardian_type="mother",
        trait="patient",
        seed=2,
    ),
    StoryParams(
        chamber="clock",
        goods="pears",
        visitor="dragon",
        obstacle="locked_door",
        aid="brass_key",
        hero_name="Tilda",
        hero_type="girl",
        guardian_type="father",
        trait="gentle",
        seed=3,
    ),
    StoryParams(
        chamber="clock",
        goods="cakes",
        visitor="duck",
        obstacle="dark_stair",
        aid="sunjar",
        hero_name="Finn",
        hero_type="boy",
        guardian_type="grandmother",
        trait="quick-eyed",
        seed=4,
    ),
    StoryParams(
        chamber="tapestry",
        goods="ribbons",
        visitor="page",
        obstacle="locked_door",
        aid="oil_drop",
        hero_name="Poppy",
        hero_type="girl",
        guardian_type="mother",
        trait="cheerful",
        seed=5,
    ),
]


def explain_rejection(chamber: Chamber, obstacle: Obstacle, aid: Aid) -> str:
    if not obstacle_fits(chamber, obstacle):
        return (
            f"(No story: {chamber.label} does not naturally contain the obstacle '{obstacle.label}'. "
            f"The trouble must honestly belong in that chamber.)"
        )
    if not aid_fits(obstacle, aid):
        return (
            f"(No story: {aid.label} does not really solve '{obstacle.label}'. "
            f"The helping tool must match the actual problem.)"
        )
    return "(No story: the requested combination is not reasonable in this world.)"


ASP_RULES = r"""
fits_obstacle(C, O) :- chamber(C), obstacle(O), affords(C, O).
fits_aid(O, A)      :- obstacle(O), aid(A), needs(O, K), kind(A, K).
valid(C, V, O, A)   :- chamber(C), visitor(V), obstacle(O), aid(A),
                       fits_obstacle(C, O), fits_aid(O, A).

relieved(O, A) :- fits_aid(O, A).
outcome(happy) :- relieved(O, A), chosen_obstacle(O), chosen_aid(A).
#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for chamber_id, chamber in CHAMBERS.items():
        lines.append(asp.fact("chamber", chamber_id))
        for obstacle_id in sorted(chamber.affords):
            lines.append(asp.fact("affords", chamber_id, obstacle_id))
    for visitor_id in VISITORS:
        lines.append(asp.fact("visitor", visitor_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("kind", aid_id, aid.kind))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_aid", params.aid),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not isinstance(params, StoryParams):
        raise StoryError("Outcome requested for invalid parameters.")
    if params.chamber not in CHAMBERS or params.obstacle not in OBSTACLES or params.aid not in AIDS:
        raise StoryError("Outcome requested for unknown registry ids.")
    chamber = CHAMBERS[params.chamber]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if obstacle_fits(chamber, obstacle) and aid_fits(obstacle, aid):
        return "happy"
    raise StoryError("Outcome requested for unreasonable parameters.")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for params in CURATED:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            rc = 1
            print(f"MISMATCH in outcome for curated params {params}: python={py_out} asp={asp_out}")
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child pauses on the way to sell wares and helps an embarrassed traveler in a castle chamber."
    )
    ap.add_argument("--chamber", choices=CHAMBERS)
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.chamber and args.obstacle and args.aid:
        chamber = CHAMBERS[args.chamber]
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not (obstacle_fits(chamber, obstacle) and aid_fits(obstacle, aid)):
            raise StoryError(explain_rejection(chamber, obstacle, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.chamber is None or combo[0] == args.chamber)
        and (args.visitor is None or combo[1] == args.visitor)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chamber_id, visitor_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    goods_id = args.goods or rng.choice(sorted(GOODS))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    guardian_type = args.guardian or rng.choice(GUARDIANS)
    trait = rng.choice(TRAITS)

    return StoryParams(
        chamber=chamber_id,
        goods=goods_id,
        visitor=visitor_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_type=guardian_type,
        trait=trait,
    )


def _cloak_ready_text(hero: Entity) -> str:
    return hero.pronoun("possessive")


def generate(params: StoryParams) -> StorySample:
    if params.chamber not in CHAMBERS:
        raise StoryError(f"Unknown chamber: {params.chamber}")
    if params.goods not in GOODS:
        raise StoryError(f"Unknown goods: {params.goods}")
    if params.visitor not in VISITORS:
        raise StoryError(f"Unknown visitor: {params.visitor}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.aid not in AIDS:
        raise StoryError(f"Unknown aid: {params.aid}")
    if params.guardian_type not in GUARDIANS:
        raise StoryError(f"Unknown guardian: {params.guardian_type}")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError(f"Unknown hero type: {params.hero_type}")

    chamber = CHAMBERS[params.chamber]
    goods = GOODS[params.goods]
    visitor = VISITORS[params.visitor]
    obstacle = OBSTACLES[params.obstacle]
    aid = copy.deepcopy(AIDS[params.aid])

    if not (obstacle_fits(chamber, obstacle) and aid_fits(obstacle, aid)):
        raise StoryError(explain_rejection(chamber, obstacle, aid))

    if aid.id == "cloak":
        hero_pos = "her" if params.hero_type == "girl" else "his"
        aid.act = aid.act.format(hero_pos=hero_pos)

    world = tell(
        chamber=chamber,
        goods=goods,
        visitor_cfg=visitor,
        obstacle=obstacle,
        aid=aid,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guardian_type=params.guardian_type,
    )
    world.get("hero").traits.append(params.trait)

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
        print(f"{len(combos)} compatible (chamber, visitor, obstacle, aid) combos:\n")
        for chamber, visitor, obstacle, aid in combos:
            print(f"  {chamber:9} {visitor:8} {obstacle:11} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.hero_name}: {p.visitor} in {p.chamber} "
                f"({p.obstacle} -> {p.aid})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
