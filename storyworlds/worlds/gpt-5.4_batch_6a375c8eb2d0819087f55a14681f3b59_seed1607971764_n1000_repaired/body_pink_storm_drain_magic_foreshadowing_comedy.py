#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py
================================================================================

A small story world about a child who loses something pink into a storm drain,
nearly does something unsafe with their whole body, and then gets help from a
ridiculous little magical drain creature. The comedy comes from the helper's
manners and the fizzy, burpy drain magic; the foreshadowing comes from odd
hints earlier in the scene that the storm drain is not ordinary at all.

This world only tells *reasonable* versions of the premise. A retrieval plan
must be both safe and actually suited to the lost object:

- a magnet works for magnetic things
- an umbrella hook works for things with a loop or handle
- a rain-burp spell works only for light floating things
- unsafe plans like climbing into the drain are known to the world but refused

Run it
------
    python storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py
    python storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py --item lunchbox --method magnet --helper eel
    python storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py --method climb_in
    python storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/body_pink_storm_drain_magic_foreshadowing_comedy.py --verify
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
class LostThing:
    id: str
    label: str
    phrase: str
    buoyant: bool
    magnetic: bool
    hookable: bool
    light: bool
    slip_text: str
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
class Helper:
    id: str
    label: str
    title: str
    foreshadow: str
    entrance: str
    quirk: str
    supports: str
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
class Method:
    id: str
    sense: int
    text: str
    qa_text: str
    unsafe: bool = False
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


def _r_lost_means_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    if item and item.meters["lost"] >= THRESHOLD:
        for kid_id in ("hero", "friend"):
            if kid_id not in world.entities:
                continue
            sig = ("worry", kid_id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get(kid_id).memes["worry"] += 1
        drain = world.entities.get("drain")
        if drain is not None and ("danger", "lost") not in world.fired:
            world.fired.add(("danger", "lost"))
            drain.meters["danger"] += 1
    return out


def _r_body_near_drain(world: World) -> list[str]:
    hero = world.entities.get("hero")
    drain = world.entities.get("drain")
    if hero is None or drain is None:
        return []
    if hero.meters["leaning"] < THRESHOLD:
        return []
    sig = ("leaning_danger", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    drain.meters["danger"] += 1
    hero.memes["fear"] += 1
    return ["__danger__"]


def _r_magic_return(world: World) -> list[str]:
    item = world.entities.get("item")
    helper = world.entities.get("helper")
    if item is None or helper is None:
        return []
    if item.meters["returned"] < THRESHOLD:
        return []
    for ent_id in ("hero", "friend"):
        if ent_id in world.entities:
            world.get(ent_id).memes["relief"] += 1
            world.get(ent_id).memes["joy"] += 1
    helper.memes["proud"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="lost_means_worry", tag="emotional", apply=_r_lost_means_worry),
    Rule(name="body_near_drain", tag="physical", apply=_r_body_near_drain),
    Rule(name="magic_return", tag="resolution", apply=_r_magic_return),
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


def method_works(item: LostThing, method: Method, helper: Helper) -> bool:
    if method.unsafe or method.sense < SENSE_MIN:
        return False
    if helper.supports != method.id:
        return False
    if method.id == "magnet":
        return item.magnetic
    if method.id == "umbrella_hook":
        return item.hookable
    if method.id == "rain_burp":
        return item.buoyant and item.light
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for method_id, method in METHODS.items():
            if method.unsafe or method.sense < SENSE_MIN:
                continue
            for helper_id, helper in HELPERS.items():
                if method_works(item, method, helper):
                    combos.append((item_id, method_id, helper_id))
    return combos


def predict_reach_risk(world: World) -> dict:
    sim = world.copy()
    if "hero" not in sim.entities:
        return {"danger": 0.0}
    sim.get("hero").meters["leaning"] += 1
    propagate(sim, narrate=False)
    return {"danger": sim.get("drain").meters["danger"]}


def foreshadow(world: World, hero: Entity, friend: Entity, item_cfg: LostThing, helper_cfg: Helper) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["giggles"] += 1
    world.say(
        f"After a rainy afternoon, {hero.id} and {friend.id} skipped along the curb beside a storm drain. "
        f"{hero.id} carried {item_cfg.phrase}, and the drain gave a tiny ridiculous sound, almost like a hiccup in a trumpet."
    )
    world.say(
        f"{helper_cfg.foreshadow} {friend.id} stopped, blinked, and said, "
        f'"Did that drain just clear its throat?"'
    )


def play(world: World, hero: Entity, friend: Entity, item_cfg: LostThing) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"Catch my {item_cfg.label}!" {hero.id} laughed. The {item_cfg.label} bounced once, twice, and then chose the worst possible direction.'
    )


def lose_item(world: World, hero: Entity, friend: Entity, item: Entity, item_cfg: LostThing) -> None:
    item.meters["lost"] += 1
    world.facts["slip_text"] = item_cfg.slip_text
    propagate(world, narrate=False)
    world.say(
        f"{item_cfg.slip_text} It dropped through the bars with a comic plunk and vanished into the storm drain."
    )
    world.say(
        f"{hero.id} and {friend.id} stared down into the dark. Somewhere below, water made a burbly slosh, as if the drain were trying not to laugh."
    )


def lunge(world: World, hero: Entity, friend: Entity) -> None:
    pred = predict_reach_risk(world)
    world.facts["predicted_danger"] = pred["danger"]
    hero.meters["leaning"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I can reach it!" {hero.id} said, dropping to {hero.pronoun("possessive")} knees and starting to slide {hero.pronoun("possessive")} body toward the opening.'
    )
    if pred["danger"] >= 2:
        world.say(
            f"{friend.id} grabbed the back of {hero.id}'s shirt at once. "
            f'"No way. Bodies stay out of storm drains," {friend.pronoun()} said.'
        )
    else:
        world.say(
            f'{friend.id} made a face and tugged {hero.id} back. "No way. Bodies stay out of storm drains."'
        )


def adult_warns(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["caution"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{hero.id}'s {parent.label_word} hurried over from the sidewalk. "
        f'"Feet back. Hands back. Whole body back," {parent.pronoun()} said, trying very hard not to sound scared.'
    )
    world.say(
        f'"Storm drains are for rainwater, not for children."'
    )


def call_magic(world: World, hero: Entity, friend: Entity, helper_cfg: Helper, method_cfg: Method) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Then the silly hint from before made sense. {friend.id} crouched safely beside the grate and whispered, "
        f'"What if the drain really was listening?"'
    )
    world.say(
        f'{hero.id} took a breath and said, "Hello? We are not sending a body down there. '
        f'Could somebody help us the safe way?"'
    )
    world.say(helper_cfg.entrance)
    world.say(
        f'The little {helper_cfg.title} blinked up at them and announced, "{helper_cfg.quirk}"'
    )
    if method_cfg.id == "magnet":
        world.say(
            f'{parent_or_friend_line(world)} the plan was a magnet tied to a string, lowered from above while everyone stayed on the street.'
        )
    elif method_cfg.id == "umbrella_hook":
        world.say(
            f'{parent_or_friend_line(world)} they tipped an umbrella upside down and used its curved handle like a careful little hook.'
        )
    elif method_cfg.id == "rain_burp":
        world.say(
            f'{parent_or_friend_line(world)} the helper puffed up like a bubble and promised one grand rain-burp, but only if everyone kept their noses and knees out of the drain.'
        )


def parent_or_friend_line(world: World) -> str:
    parent = world.get("parent")
    return f'{parent.label_word.capitalize()} nodded, so'


def retrieve(world: World, hero: Entity, friend: Entity, parent: Entity,
             item: Entity, item_cfg: LostThing, helper: Entity,
             helper_cfg: Helper, method_cfg: Method) -> None:
    item.meters["returned"] += 1
    item.meters["lost"] = 0.0
    helper.memes["helping"] += 1
    world.facts["retrieval_success"] = True
    propagate(world, narrate=False)
    if method_cfg.id == "magnet":
        world.say(
            f"The magnet bumped the water, wobbled once, and then clicked onto the {item_cfg.label}. "
            f'The {helper_cfg.title} gave the string a smart little tug, and up came the prize, dripping and triumphant.'
        )
    elif method_cfg.id == "umbrella_hook":
        world.say(
            f"The umbrella handle slid under the {item_cfg.label}, the little helper puffed its cheeks, and together they lifted it neatly through the bars."
        )
    elif method_cfg.id == "rain_burp":
        world.say(
            f'The {helper_cfg.title} inflated like a pink soap bubble and let out one enormous polite burp. '
            f'A round splash of water bounced upward, carrying the {item_cfg.label} right back to the curb.'
        )
    world.say(
        f"{hero.id} clapped. {friend.id} laughed so hard {friend.pronoun()} had to sit down on the dry part of the sidewalk."
    )
    world.say(
        f'{parent.label_word.capitalize()} handed the {item_cfg.label} back to {hero.id} and said, '
        f'"That is how we solve a problem: with help, with tools, and with every bit of your body staying out of the drain."'
    )


def ending(world: World, hero: Entity, friend: Entity, helper_cfg: Helper, item_cfg: LostThing) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"The drain gurgled one last satisfied note. Before ducking away, the {helper_cfg.title} saluted with a tiny splash and disappeared."
    )
    world.say(
        f"On the walk home, {hero.id} tucked the {item_cfg.label} under {hero.pronoun('possessive')} arm and kept peeking at every grate. "
        f"Now the storm drain looked less like a hole for climbing into and more like a place where very odd neighbors might live."
    )
    world.say(
        f"And whenever the street made a burbly little sound after rain, both children grinned and checked that their feet stayed on top of the sidewalk."
    )


def tell(item_cfg: LostThing, helper_cfg: Helper, method_cfg: Method,
         hero_name: str = "Mia", hero_type: str = "girl",
         friend_name: str = "Ben", friend_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, role="hero", label=hero_name))
    hero.attrs["name"] = hero_name
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, role="friend", label=friend_name))
    friend.attrs["name"] = friend_name
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    drain = world.add(Entity(id="drain", kind="thing", type="storm_drain", label="storm drain"))
    item = world.add(Entity(id="item", kind="thing", type="lost_thing", label=item_cfg.label))
    helper = world.add(Entity(id="helper", kind="character", type="magic_helper", label=helper_cfg.label))
    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name
    world.facts["item_cfg"] = item_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["method_cfg"] = method_cfg
    world.facts["safe"] = True
    world.facts["retrieval_success"] = False
    world.facts["predicted_danger"] = 0.0

    foreshadow(world, hero, friend, item_cfg, helper_cfg)
    play(world, hero, friend, item_cfg)

    world.para()
    lose_item(world, hero, friend, item, item_cfg)
    lunge(world, hero, friend)
    adult_warns(world, parent, hero)

    world.para()
    call_magic(world, hero, friend, helper_cfg, method_cfg)
    retrieve(world, hero, friend, parent, item, item_cfg, helper, helper_cfg, method_cfg)

    world.para()
    ending(world, hero, friend, helper_cfg, item_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        drain=drain,
        item=item,
        helper=helper,
    )
    return world


ITEMS = {
    "ball": LostThing(
        id="ball",
        label="pink ball",
        phrase="a shiny pink ball",
        buoyant=True,
        magnetic=False,
        hookable=False,
        light=True,
        slip_text="The pink ball kissed the curb, spun in a wild little circle, and escaped.",
        tags={"ball", "pink", "floating"},
    ),
    "boot": LostThing(
        id="boot",
        label="pink rain boot",
        phrase="one bright pink rain boot with a loop on the back",
        buoyant=True,
        magnetic=False,
        hookable=True,
        light=True,
        slip_text="The loose boot flopped off a foot, skated over a puddle, and dove like it had somewhere important to be.",
        tags={"boot", "pink", "hook"},
    ),
    "lunchbox": LostThing(
        id="lunchbox",
        label="pink lunchbox",
        phrase="a small pink lunchbox with a clanky clasp",
        buoyant=False,
        magnetic=True,
        hookable=True,
        light=False,
        slip_text="The lunchbox tipped off the curb, bonked the grate with a clang, and slid down into the dark.",
        tags={"lunchbox", "pink", "magnet", "hook"},
    ),
    "robot": LostThing(
        id="robot",
        label="pink robot",
        phrase="a tiny pink wind-up robot",
        buoyant=False,
        magnetic=True,
        hookable=False,
        light=True,
        slip_text="The little robot marched straight off the edge as if it had made a terrible decision all by itself.",
        tags={"robot", "pink", "magnet"},
    ),
}

HELPERS = {
    "dragon": Helper(
        id="dragon",
        label="the drain dragon",
        title="drain dragon",
        foreshadow="A faint pink bubble floated out of the grate and popped on the air.",
        entrance="With a ripple and a sneezy puff, a tiny dragon made of rainwater and sparkle-light peeked up between the bars.",
        quirk="I only perform heroics after proper introductions and absolutely never before snacks.",
        supports="rain_burp",
        tags={"magic", "dragon", "rain_burp"},
    ),
    "eel": Helper(
        id="eel",
        label="the echo eel",
        title="echo eel",
        foreshadow='From below came a soft metallic "ting... ting..." as if someone were tapping a spoon on a cup.',
        entrance="A silver-blue eel with whiskers like commas swam up through the shadow and looped around a floating string.",
        quirk="I adore neat solutions and very dramatic pauses.",
        supports="magnet",
        tags={"magic", "eel", "magnet"},
    ),
    "newt": Helper(
        id="newt",
        label="the giggle newt",
        title="giggle newt",
        foreshadow="A tiny laugh bubbled up from the grate, then pretended it had been only water.",
        entrance="A spotted newt in a leaf-vest popped up and balanced on the lowest bar like a stage performer.",
        quirk="If there is a hook involved, I insist on calling it a rescue swoop.",
        supports="umbrella_hook",
        tags={"magic", "newt", "hook"},
    ),
}

METHODS = {
    "magnet": Method(
        id="magnet",
        sense=3,
        text="use a magnet on a string from above",
        qa_text="They used a magnet on a string from above, so nobody had to climb into the drain.",
        tags={"magnet", "tool"},
    ),
    "umbrella_hook": Method(
        id="umbrella_hook",
        sense=3,
        text="use an umbrella handle as a careful hook",
        qa_text="They used an umbrella handle like a hook from the sidewalk, which kept everybody safely out of the drain.",
        tags={"hook", "tool", "umbrella"},
    ),
    "rain_burp": Method(
        id="rain_burp",
        sense=3,
        text="ask for a rain-burp spell to splash the item back up",
        qa_text="They asked the magical helper for a rain-burp spell, and the water popped the item back to the curb while the children stayed out of danger.",
        tags={"magic", "spell"},
    ),
    "climb_in": Method(
        id="climb_in",
        sense=0,
        text="climb into the storm drain",
        qa_text="Nobody should climb into a storm drain.",
        unsafe=True,
        tags={"unsafe", "body"},
    ),
    "hand_reach": Method(
        id="hand_reach",
        sense=1,
        text="reach farther and farther by hand",
        qa_text="Reaching deeper into a storm drain is unsafe.",
        unsafe=True,
        tags={"unsafe", "body"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Eli", "Noah"]


@dataclass
class StoryParams:
    item: str
    method: str
    helper: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent_type: str
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
        item="ball",
        method="rain_burp",
        helper="dragon",
        hero_name="Mia",
        hero_type="girl",
        friend_name="Ben",
        friend_type="boy",
        parent_type="mother",
    ),
    StoryParams(
        item="lunchbox",
        method="magnet",
        helper="eel",
        hero_name="Leo",
        hero_type="boy",
        friend_name="Ava",
        friend_type="girl",
        parent_type="father",
    ),
    StoryParams(
        item="boot",
        method="umbrella_hook",
        helper="newt",
        hero_name="Nora",
        hero_type="girl",
        friend_name="Sam",
        friend_type="boy",
        parent_type="mother",
    ),
    StoryParams(
        item="robot",
        method="magnet",
        helper="eel",
        hero_name="Theo",
        hero_type="boy",
        friend_name="Lucy",
        friend_type="girl",
        parent_type="father",
    ),
]


KNOWLEDGE = {
    "storm_drain": [
        (
            "What is a storm drain?",
            "A storm drain is an opening by the curb that carries rainwater away. It is not a place for children to climb into.",
        )
    ],
    "body": [
        (
            "Why should you keep your whole body out of a storm drain?",
            "A storm drain is dark, slippery, and not made for people. The safe choice is to stay above it and ask a grown-up for help.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls on some kinds of metal. That can help lift a metal thing without reaching down with your hands.",
        )
    ],
    "umbrella": [
        (
            "How can an umbrella help reach something safely?",
            "Its curved handle can sometimes catch a loop or handle from above. A grown-up should help so everybody stays steady and safe.",
        )
    ],
    "floating": [
        (
            "Why do some toys float?",
            "Some things are light and shaped so water can hold them up. If they float, they can bob instead of sinking.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something impossible that happens inside a pretend story world. It can make a problem funny or surprising, like a talking drain helper.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a little hint early in the story that points to something important later. A strange bubble or laugh can warn you that magic is coming.",
        )
    ],
    "pink": [
        (
            "What color is pink?",
            "Pink is a light reddish color. In this story world, the lost thing is always pink so it is easy to notice and remember.",
        )
    ],
}
KNOWLEDGE_ORDER = ["storm_drain", "body", "pink", "magic", "foreshadowing", "magnet", "umbrella", "floating"]


def generation_prompts(world: World) -> list[str]:
    item_cfg = world.facts["item_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    method_cfg = world.facts["method_cfg"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write a funny story for a 3-to-5-year-old set by a storm drain that includes the words "body" and "pink".',
        f"Tell a magical comedy where {hero.attrs['name']} loses {item_cfg.phrase}, almost leans {hero.pronoun('possessive')} body into a storm drain, and gets help from {helper_cfg.label} using {method_cfg.text}.",
        "Write a story with foreshadowing where strange drain sounds hint that a silly magical helper is about to appear, and end with the children learning the safe way to solve the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    item_cfg = world.facts["item_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    method_cfg = world.facts["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']} and {friend.attrs['name']}, two children by a storm drain, plus {hero.attrs['name']}'s {parent.label_word} and a magical helper. The trouble starts when a pink object slips through the grate.",
        ),
        (
            f"What fell into the storm drain?",
            f"It was {item_cfg.phrase}. The pink object slipped through the bars and vanished into the dark water below.",
        ),
        (
            f"Why did {friend.attrs['name']} stop {hero.attrs['name']}?",
            f"{friend.attrs['name']} stopped {hero.attrs['name']} because {hero.pronoun('possessive')} body was starting to slide toward the storm drain. That was dangerous, so {friend.pronoun()} pulled {hero.pronoun('object')} back and said bodies stay out of drains.",
        ),
        (
            "What was the foreshadowing in the story?",
            f"The strange sound and {helper_cfg.foreshadow[:-1].lower()} were little hints that the drain was magical. Those clues mattered later when {helper_cfg.label} appeared to help.",
        ),
        (
            "How did they get the lost thing back?",
            f"{method_cfg.qa_text} The plan worked because it matched the kind of item that had fallen into the drain.",
        ),
        (
            "How did the story end?",
            f"The children got the pink object back, laughed, and walked home wiser. The ending shows they had changed because they kept their bodies out of the storm drain and looked for safe help instead.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    method_cfg = world.facts["method_cfg"]
    tags = {"storm_drain", "body", "pink", "magic", "foreshadowing"}
    if item_cfg.buoyant:
        tags.add("floating")
    if method_cfg.id == "magnet":
        tags.add("magnet")
    if method_cfg.id == "umbrella_hook":
        tags.add("umbrella")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    if method.unsafe or method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it is unsafe for a child-sized body near a storm drain. "
            f"Choose a safe retrieval plan like magnet, umbrella_hook, or rain_burp.)"
        )
    return f"(Refusing method '{method_id}': it is not considered a safe plan here.)"


def explain_combo_rejection(item: LostThing, method: Method, helper: Helper) -> str:
    if helper.supports != method.id:
        return (
            f"(No story: {helper.label} does not use the '{method.id}' method. "
            f"Pick a helper that matches the retrieval plan.)"
        )
    if method.id == "magnet" and not item.magnetic:
        return (
            f"(No story: {item.phrase} is not magnetic, so a magnet cannot pull it out of the storm drain.)"
        )
    if method.id == "umbrella_hook" and not item.hookable:
        return (
            f"(No story: {item.phrase} has nothing safe to hook from above, so an umbrella handle would not catch it.)"
        )
    if method.id == "rain_burp" and not (item.buoyant and item.light):
        return (
            f"(No story: the rain-burp spell only pops up light floating things, and {item.phrase} does not fit that.)"
        )
    return "(No story: this combination does not make sense in this world.)"


ASP_RULES = r"""
safe_method(M) :- method(M), sense(M,S), sense_min(Min), S >= Min, not unsafe(M).
works(I, magnet, H) :- item(I), helper(H), supports(H, magnet), magnetic(I).
works(I, umbrella_hook, H) :- item(I), helper(H), supports(H, umbrella_hook), hookable(I).
works(I, rain_burp, H) :- item(I), helper(H), supports(H, rain_burp), buoyant(I), light(I).
valid(I, M, H) :- works(I, M, H), safe_method(M).
success(I, M, H) :- valid(I, M, H).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.buoyant:
            lines.append(asp.fact("buoyant", item_id))
        if item.magnetic:
            lines.append(asp.fact("magnetic", item_id))
        if item.hookable:
            lines.append(asp.fact("hookable", item_id))
        if item.light:
            lines.append(asp.fact("light", item_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.unsafe:
            lines.append(asp.fact("unsafe", method_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("supports", helper_id, helper.supports))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            generate(params)
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            break
    else:
        print(f"OK: curated generation succeeded on {len(CURATED)} stories.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pink thing, a storm drain, a magical helper, and a safe joke-filled rescue."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid item/method/helper combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and (METHODS[args.method].unsafe or METHODS[args.method].sense < SENSE_MIN):
        raise StoryError(explain_method_rejection(args.method))

    if args.item and args.method and args.helper:
        item_cfg = ITEMS[args.item]
        method_cfg = METHODS[args.method]
        helper_cfg = HELPERS[args.helper]
        if not method_works(item_cfg, method_cfg, helper_cfg):
            raise StoryError(explain_combo_rejection(item_cfg, method_cfg, helper_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.method is None or combo[1] == args.method)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, method_id, helper_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(
        item=item_id,
        method=method_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")

    item_cfg = ITEMS[params.item]
    method_cfg = METHODS[params.method]
    helper_cfg = HELPERS[params.helper]

    if method_cfg.unsafe or method_cfg.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not method_works(item_cfg, method_cfg, helper_cfg):
        raise StoryError(explain_combo_rejection(item_cfg, method_cfg, helper_cfg))

    world = tell(
        item_cfg=item_cfg,
        helper_cfg=helper_cfg,
        method_cfg=method_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent_type,
    )
    world.get("hero").attrs["name"] = params.hero_name
    world.get("friend").attrs["name"] = params.friend_name

    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("friend", params.friend_name),
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
        print(f"{len(combos)} compatible (item, method, helper) combos:\n")
        for item_id, method_id, helper_id in combos:
            print(f"  {item_id:10} {method_id:14} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.item} with {p.method} via {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
