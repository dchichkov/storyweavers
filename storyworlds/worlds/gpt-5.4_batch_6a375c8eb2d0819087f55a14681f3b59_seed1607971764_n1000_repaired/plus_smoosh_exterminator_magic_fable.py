#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py
==================================================================

A standalone story world in a gentle fable style: a small animal uses a magic
"plus" charm to make one more treat for the market, the treats tip and go
"smoosh," hungry pests rush in, and a kindly exterminator helps set things
right. The world enforces a simple commonsense rule: only soft, sweet treats on
open, tippy surfaces can make the sort of sticky mess that would honestly draw
pests and need an exterminator at all.

Run it
------
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py --treat plum_tarts --surface tray --pest ants
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py --treat seed_cakes --surface tin
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py --all
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/plus_smoosh_exterminator_magic_fable.py --verify
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
        female = {"girl", "hen", "sheep", "doe", "vixen", "mother"}
        male = {"boy", "fox", "mole", "toad", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Treat:
    id: str
    label: str
    phrase: str
    plural_label: str
    squish: int
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
class Surface:
    id: str
    label: str
    phrase: str
    spill: int
    closed: bool = False
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
class Pest:
    id: str
    label: str
    arrive: str
    plural: bool = True
    likes: set[str] = field(default_factory=set)
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_sticky(world: World) -> list[str]:
    pile = world.get("pile")
    floor = world.get("floor")
    if pile.meters["fallen"] < THRESHOLD:
        return []
    sig = ("sticky", int(pile.meters["fallen"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    floor.meters["sticky"] += max(1, int(world.facts["treat_cfg"].squish))
    return ["__sticky__"]


def _r_pests(world: World) -> list[str]:
    floor = world.get("floor")
    stall = world.get("stall")
    hero = world.get("hero")
    friend = world.get("friend")
    pest_cfg = world.facts["pest_cfg"]
    if floor.meters["sticky"] < THRESHOLD:
        return []
    sig = ("pests", pest_cfg.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stall.meters["pests"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    return ["__pests__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="sticky", tag="physical", apply=_r_sticky),
    Rule(name="pests", tag="social", apply=_r_pests),
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


def hazard_at_risk(treat: Treat, surface: Surface, pest: Pest) -> bool:
    if surface.closed:
        return False
    if treat.squish + surface.spill < 2:
        return False
    return bool(treat.tags & pest.likes)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(treat: Treat, surface: Surface, delay: int) -> int:
    return treat.squish + surface.spill + delay


def is_contained(response: Response, treat: Treat, surface: Surface, delay: int) -> bool:
    return response.power >= severity_of(treat, surface, delay)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    do_plus(sim, narrate=False)
    return {
        "fallen": sim.get("pile").meters["fallen"],
        "sticky": sim.get("floor").meters["sticky"],
        "pests": sim.get("stall").meters["pests"],
    }


def introduce(world: World, hero: Entity, friend: Entity, treat: Treat) -> None:
    world.say(
        f"In the mossy market under the old chestnut tree, {hero.id} the little "
        f"{hero.type} set out {treat.plural_label} to sell with {friend.id}. "
        f"In that valley, small creatures did business politely, and magic was "
        f"used only when it truly helped."
    )


def show_plus_charm(world: World, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"Tied to {hero.pronoun('possessive')} apron was a silver charm shaped "
        f"like a tiny plus sign. When tapped once and spoken to kindly, it could "
        f"make one more of a good thing."
    )


def quiet_market(world: World, hero: Entity, treat: Treat, surface: Surface) -> None:
    world.say(
        f"That morning the market was slow, and {hero.id} looked at the "
        f"{surface.label} holding {treat.plural_label}. "
        f'"If I had just one more, perhaps one more customer would smile," '
        f"{hero.pronoun()} whispered."
    )


def warn(world: World, friend: Entity, hero: Entity, treat: Treat, surface: Surface, pest: Pest) -> None:
    pred = predict_spill(world)
    world.facts["predicted_sticky"] = pred["sticky"]
    world.facts["predicted_pests"] = pred["pests"]
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} flicked an ear and studied the {surface.label}. '
        f'"Be gentle with the plus charm," {friend.pronoun()} said. '
        f'"{surface.phrase.capitalize()} is already full, and {treat.plural_label} are soft. '
        f'If one slides, it will go smoosh on the floor, and {pest.label} will come."'
    )


def decide(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"But wishing can sound wise when it wears a shiny coat. {hero.id} "
        f"thought of full baskets, warm praise, and easy coins, and forgot that "
        f"enough is also a kind of riches."
    )


def do_plus(world: World, narrate: bool = True) -> None:
    pile = world.get("pile")
    treat = world.facts["treat_cfg"]
    surface = world.facts["surface_cfg"]
    pile.meters["count"] += 1
    if treat.squish + surface.spill >= 2:
        pile.meters["fallen"] += 1
    propagate(world, narrate=narrate)


def cast_plus(world: World, hero: Entity, treat: Treat, surface: Surface) -> None:
    do_plus(world, narrate=False)
    hero.memes["regret"] += 1
    pile = world.get("pile")
    if pile.meters["fallen"] >= THRESHOLD:
        world.say(
            f'{hero.id} tapped the charm and said, "plus." For one blink, an extra '
            f"{treat.label} shone on the edge of {surface.phrase}. Then the stack "
            f"tilted, slipped, and went smoosh on the floor."
        )
    else:
        world.say(
            f'{hero.id} tapped the charm and said, "plus," and one more '
            f"{treat.label} appeared neatly where there was room."
        )


def pest_arrival(world: World, pest: Pest) -> None:
    if world.get("stall").meters["pests"] >= THRESHOLD:
        world.say(
            f"Soon {pest.arrive}. Little feet and wings gathered wherever the "
            f"sweet smell spread."
        )


def call_exterminator(world: World, friend: Entity, helper: Entity) -> None:
    friend.memes["wisdom"] += 1
    world.say(
        f'"Quick," said {friend.id}, "call {helper.id}, the village exterminator." '
        f"In that valley, an exterminator was not a harsh destroyer but a keeper "
        f"of balance, one who guided hungry pests away from places where they did not belong."
    )


def rescue(world: World, helper: Entity, response: Response, pest: Pest) -> None:
    world.get("stall").meters["pests"] = 0.0
    world.get("floor").meters["sticky"] = 0.0
    body = response.text.replace("{pest}", pest.label)
    world.say(
        f"{helper.id} came at once, bowed to the stall, and {body}."
    )
    world.say(
        f"The busy {pest.label} turned aside, the sweet smell faded, and the "
        f"market breathed easily again."
    )


def lesson(world: World, helper: Entity, hero: Entity, treat: Treat, surface: Surface) -> None:
    hero.memes["wisdom"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f'Then {helper.id} touched the little plus charm and said, '
        f'"Magic is brightest when it minds the shape of things. '
        f'{surface.phrase.capitalize()} can hold only so much, and soft '
        f'{treat.plural_label} ask for a steady place."'
    )
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head, then lifted it "
        f"again with honest eyes. From that moment on, {hero.pronoun()} wished "
        f"not for more than enough, but for enough well kept."
    )


def safe_change(world: World, hero: Entity, friend: Entity, treat: Treat) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"That afternoon {hero.id} set the next batch in a tall blue tin before "
        f"using even a whisper of magic. The {treat.plural_label} stayed tidy, "
        f"and {friend.id} smiled to see wisdom sitting beside wonder."
    )
    world.say(
        f"So the stall shone, the chestnut leaves nodded overhead, and every "
        f"customer went home with a sweet and a story: plus is a lovely word, "
        f"but only when joined to care."
    )


def rescue_fail(world: World, helper: Entity, response: Response, pest: Pest) -> None:
    world.get("stall").meters["pests"] += 1
    world.get("floor").meters["sticky"] += 1
    body = response.fail.replace("{pest}", pest.label)
    world.say(
        f"{helper.id} hurried over and {body}."
    )
    world.say(
        f"But the smell of sugar had already traveled farther than one kind spell could reach, "
        f"and more {pest.label} kept coming."
    )


def close_market(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["sorrow"] += 1
    friend.memes["care"] += 1
    world.say(
        f"The neighbors helped {hero.id} and {friend.id} carry the stall cloths away "
        f"so the market row could be cleaned. No one was hurt, yet the little stall "
        f"had to close for the day."
    )


def sad_lesson(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f'"Remember this," said {helper.id} gently. "A hurried bit of magic can make '
        f'a small mess grow large, and a small wish grow costly."'
    )
    world.say(
        f"{hero.id} kept the plus charm in a pocket after that until {hero.pronoun()} "
        f"had room, patience, and a steadier heart."
    )
    world.say(
        "And that is why, in the mossy market, merchants still say that the quickest extra "
        "is often the dearest."
    )


def tell(
    treat: Treat,
    surface: Surface,
    pest: Pest,
    response: Response,
    hero_name: str = "Pip",
    hero_type: str = "fox",
    friend_name: str = "Mira",
    friend_type: str = "hen",
    helper_name: str = "Master Mole",
    helper_type: str = "mole",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    stall = world.add(Entity(id="stall", type="stall", label="the stall"))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    pile = world.add(Entity(id="pile", type="pile", label=treat.plural_label))
    pile.meters["count"] = 3.0
    pile.attrs["surface"] = surface.id

    world.facts.update(
        treat_cfg=treat,
        surface_cfg=surface,
        pest_cfg=pest,
        response=response,
        hero=hero,
        friend=friend,
        helper=helper,
        delay=delay,
    )

    introduce(world, hero, friend, treat)
    show_plus_charm(world, hero)
    quiet_market(world, hero, treat, surface)

    world.para()
    warn(world, friend, hero, treat, surface, pest)
    decide(world, hero)
    cast_plus(world, hero, treat, surface)
    pest_arrival(world, pest)
    call_exterminator(world, friend, helper)

    contained = is_contained(response, treat, surface, delay)
    outcome = "contained" if contained else "lost"

    world.para()
    if contained:
        rescue(world, helper, response, pest)
        lesson(world, helper, hero, treat, surface)
        world.para()
        safe_change(world, hero, friend, treat)
    else:
        rescue_fail(world, helper, response, pest)
        close_market(world, hero, friend)
        sad_lesson(world, helper, hero)

    world.facts.update(
        outcome=outcome,
        severity=severity_of(treat, surface, delay),
        spill_happened=world.get("pile").meters["fallen"] >= THRESHOLD,
        pests_arrived=world.get("stall").meters["pests"] >= THRESHOLD or outcome == "lost",
        contained=contained,
    )
    return world


TREATS = {
    "plum_tarts": Treat(
        id="plum_tarts",
        label="plum tart",
        phrase="a tray of little plum tarts",
        plural_label="plum tarts",
        squish=2,
        tags={"sweet", "sticky", "plum"},
    ),
    "honey_buns": Treat(
        id="honey_buns",
        label="honey bun",
        phrase="a basket of honey buns",
        plural_label="honey buns",
        squish=2,
        tags={"sweet", "sticky", "honey"},
    ),
    "berry_cakes": Treat(
        id="berry_cakes",
        label="berry cake",
        phrase="a row of berry cakes",
        plural_label="berry cakes",
        squish=1,
        tags={"sweet", "sticky", "berry"},
    ),
    "seed_cakes": Treat(
        id="seed_cakes",
        label="seed cake",
        phrase="a plate of seed cakes",
        plural_label="seed cakes",
        squish=0,
        tags={"crumbly", "seed"},
    ),
}

SURFACES = {
    "tray": Surface(
        id="tray",
        label="tray",
        phrase="the shallow copper tray",
        spill=2,
        closed=False,
        tags={"open_surface", "tray"},
    ),
    "basket": Surface(
        id="basket",
        label="basket",
        phrase="the woven basket",
        spill=1,
        closed=False,
        tags={"open_surface", "basket"},
    ),
    "plate": Surface(
        id="plate",
        label="plate",
        phrase="the polished plate",
        spill=1,
        closed=False,
        tags={"open_surface", "plate"},
    ),
    "tin": Surface(
        id="tin",
        label="tin",
        phrase="the tall blue tin",
        spill=0,
        closed=True,
        tags={"closed_surface", "tin"},
    ),
}

PESTS = {
    "ants": Pest(
        id="ants",
        label="ants",
        arrive="a black line of ants came marching from the clover edge",
        plural=True,
        likes={"sticky", "sweet"},
        tags={"ants", "sticky"},
    ),
    "flies": Pest(
        id="flies",
        label="flies",
        arrive="a silver-buzzing cloud of flies circled down from the sunny air",
        plural=True,
        likes={"sweet"},
        tags={"flies", "sweet_air"},
    ),
    "wasps": Pest(
        id="wasps",
        label="wasps",
        arrive="two nosy wasps dipped low, then more followed the smell",
        plural=True,
        likes={"sweet"},
        tags={"wasps", "sweet_air"},
    ),
}

RESPONSES = {
    "peppermint_circle": Response(
        id="peppermint_circle",
        sense=3,
        power=3,
        text="drew a peppermint circle, swept up the crumbs, and guided the {pest} toward the herb patch beyond the market",
        fail="drew a peppermint circle, but the sweetness had spread beyond its edge and the {pest} only swirled around it",
        qa_text="drew a peppermint circle, swept the mess, and guided the pests away",
        tags={"peppermint", "gentle_exterminator"},
    ),
    "moon_bell": Response(
        id="moon_bell",
        sense=3,
        power=4,
        text="rang a small moon bell, and with each clear note the {pest} lifted and drifted back toward the wild hedge while the floor was cleaned",
        fail="rang the moon bell, but the smell was already too strong and the {pest} kept returning",
        qa_text="rang a moon bell and guided the pests away while the stall was cleaned",
        tags={"moon_bell", "gentle_exterminator"},
    ),
    "broom_only": Response(
        id="broom_only",
        sense=2,
        power=2,
        text="worked quickly with a broom and cloth until the {pest} had no sweetness left to chase",
        fail="swept with a broom and cloth, but new pests kept finding the sticky trail before the smell was gone",
        qa_text="swept the floor clean with a broom and cloth",
        tags={"broom", "cleaning"},
    ),
    "shout_and_stamp": Response(
        id="shout_and_stamp",
        sense=1,
        power=1,
        text="shouted and stamped at the {pest} until they scattered",
        fail="shouted and stamped, but the {pest} only flew up and settled again",
        qa_text="shouted and stamped at the pests",
        tags={"poor_choice"},
    ),
}

FOX_NAMES = ["Pip", "Rill", "Tarn", "Nip", "Bram"]
HEN_NAMES = ["Mira", "Lark", "Penny", "Saffy", "Dot"]
MOLE_NAMES = ["Master Mole", "Old Mole Rowan", "Moss Mole", "Mender Mole"]
HERO_TYPES = ["fox", "toad"]
FRIEND_TYPES = ["hen", "sheep"]


@dataclass
class StoryParams:
    treat: str
    surface: str
    pest: str
    response: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    helper_name: str
    helper_type: str
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
    "plus": [
        (
            "What does plus mean?",
            "Plus means adding one thing to another thing. In this story it also names a little magic charm that makes one more item appear."
        )
    ],
    "smoosh": [
        (
            "What does smoosh mean?",
            "Smoosh means something soft gets squashed flat. A soft tart that falls can go smoosh and make a sticky mess."
        )
    ],
    "exterminator": [
        (
            "What does an exterminator do in this story world?",
            "Here an exterminator is a helper who removes pests from places where they should not be. The good exterminator does it gently by cleaning the mess and guiding the pests away."
        )
    ],
    "ants": [
        (
            "Why do ants come to sweet spills?",
            "Ants look for food, and sweet sticky spills smell like an easy meal. If the mess is cleaned quickly, they stop coming."
        )
    ],
    "flies": [
        (
            "Why do flies buzz around food?",
            "Flies are drawn by smells from sweet or sticky food. Covering food and cleaning spills helps keep them away."
        )
    ],
    "wasps": [
        (
            "Why do wasps visit sweet food?",
            "Wasps often notice sugary smells and come to investigate. That is why sweet food should be kept tidy and covered."
        )
    ],
    "tin": [
        (
            "Why is a tall tin safer than a tray for soft treats?",
            "A tall tin has sides and a lid, so soft treats are less likely to slide off. A flat tray gives them much less help staying put."
        )
    ],
    "magic": [
        (
            "Why must magic be used carefully?",
            "Magic can make things happen quickly, but quick help can still cause trouble if nobody thinks ahead. Wise magic works with the shape of the world instead of against it."
        )
    ],
}
KNOWLEDGE_ORDER = ["plus", "smoosh", "exterminator", "magic", "ants", "flies", "wasps", "tin"]


def pair_noun(hero: Entity, friend: Entity) -> str:
    return f"{hero.type} and {friend.type}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    treat = f["treat_cfg"]
    surface = f["surface_cfg"]
    pest = f["pest_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old with Magic that includes the words '
        f'"plus", "smoosh", and "exterminator". The story should involve {treat.plural_label} on {surface.phrase}.'
    )
    if outcome == "contained":
        return [
            base,
            f"Tell a gentle market fable where {hero.id} uses a plus charm to make one more {treat.label}, "
            f"the treat goes smoosh, {pest.label} arrive, and {helper.id} the exterminator fixes the problem kindly.",
            f"Write a fable about wanting a little extra, then learning wisdom from a friend named {friend.id} "
            f"and a gentle exterminator after a sticky magical mistake.",
        ]
    return [
        base,
        f"Tell a cautionary fable where {hero.id} uses magic for one extra {treat.label}, the mess draws {pest.label}, "
        f"and even the exterminator cannot save the stall from closing for the day.",
        f"Write a soft, sad fable about how a hurried wish for more can spoil a market morning after a plus charm makes a sweet smoosh.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    treat = f["treat_cfg"]
    surface = f["surface_cfg"]
    pest = f["pest_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {friend.id} the {friend.type}, and {helper.id}, the village exterminator. They share a little market stall and a lesson about using magic wisely."
        ),
        (
            f"Why did {hero.id} use the plus charm?",
            f"{hero.id} hoped that one extra {treat.label} would bring one more smiling customer. The wish sounded helpful, but it came from wanting more before checking whether there was room."
        ),
        (
            f"What warning did {friend.id} give?",
            f"{friend.id} warned that {surface.phrase} was already full and the soft {treat.plural_label} could slide. {friend.pronoun().capitalize()} also knew a smoosh on the floor would draw {pest.label}."
        ),
    ]
    if f["spill_happened"]:
        qa.append(
            (
                "What happened after the magic word plus was spoken?",
                f"An extra {treat.label} appeared, but the stack tipped and went smoosh on the floor. Because the mess was sweet and sticky, {pest.label} hurried to the stall."
            )
        )
    if f["outcome"] == "contained":
        body = response.qa_text
        qa.append(
            (
                f"How did the exterminator solve the problem?",
                f"{helper.id} {body}. Cleaning the sweetness away mattered just as much as moving the pests, because once the smell was gone the stall was calm again."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn at the end?",
                f"{hero.id} learned that magic should be used with care and only when there is room for what it makes. The ending proves the lesson, because later the treats are kept safely in a tall tin before any magic is used."
            )
        )
    else:
        qa.append(
            (
                "Why did the stall have to close for the day?",
                f"The first fix was too weak for such a sticky, far-reaching mess, so more {pest.label} kept coming. No one was hurt, but the stall could not stay open until everything was properly cleaned."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn from the bad turn?",
                f"{hero.id} learned that a hurried wish for extra can cost more than it gives. After that, {hero.pronoun()} kept the plus charm tucked away until {hero.pronoun()} had patience and enough room."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"plus", "smoosh", "exterminator", "magic"}
    pest = f["pest_cfg"]
    surface = f["surface_cfg"]
    tags |= set(pest.tags)
    if surface.id == "tin":
        tags.add("tin")
    if f["outcome"] == "contained":
        if surface.id != "tin":
            tags.add("tin")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} severity={world.facts.get('severity')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for treat_id, treat in TREATS.items():
        for surface_id, surface in SURFACES.items():
            for pest_id, pest in PESTS.items():
                if hazard_at_risk(treat, surface, pest):
                    combos.append((treat_id, surface_id, pest_id))
    return combos


def explain_rejection(treat: Treat, surface: Surface, pest: Pest) -> str:
    if surface.closed:
        return (
            f"(No story: {surface.phrase.capitalize()} keeps soft sweets from sliding, so there is no honest "
            f"smoosh and no need for an exterminator. Pick an open surface like a tray or basket.)"
        )
    if treat.squish + surface.spill < 2:
        return (
            f"(No story: {treat.plural_label.capitalize()} on {surface.label} would not make a big enough smoosh "
            f"to drive the fable. Pick a softer treat or a tippier surface.)"
        )
    if not (treat.tags & pest.likes):
        return (
            f"(No story: {pest.label.capitalize()} are not the sort of pests this treat would honestly attract here. "
            f"Choose pests that like sweet or sticky spills.)"
        )
    return "(No story: this combination does not make a reasonable sticky-market problem.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of the gentler, more useful methods: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(
        RESPONSES[params.response],
        TREATS[params.treat],
        SURFACES[params.surface],
        params.delay,
    ) else "lost"


ASP_RULES = r"""
hazard(T,S,P) :- treat(T), surface(S), pest(P),
                 not closed(S),
                 squish(T,Q), spill(S,R), Q + R >= 2,
                 treat_tag(T,Tag), pest_likes(P,Tag).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,S,P) :- hazard(T,S,P).

severity(V) :- chosen_treat(T), chosen_surface(S), delay(D),
               squish(T,Q), spill(S,R), V = Q + R + D.
contained :- chosen_response(R), power(R,P), severity(V), P >= V.
outcome(contained) :- contained.
outcome(lost) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("squish", treat_id, treat.squish))
        for tag in sorted(treat.tags):
            lines.append(asp.fact("treat_tag", treat_id, tag))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        lines.append(asp.fact("spill", surface_id, surface.spill))
        if surface.closed:
            lines.append(asp.fact("closed", surface_id))
    for pest_id, pest in PESTS.items():
        lines.append(asp.fact("pest", pest_id))
        for tag in sorted(pest.likes):
            lines.append(asp.fact("pest_likes", pest_id, tag))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        treat="plum_tarts",
        surface="tray",
        pest="ants",
        response="moon_bell",
        hero_name="Pip",
        hero_type="fox",
        friend_name="Mira",
        friend_type="hen",
        helper_name="Master Mole",
        helper_type="mole",
        delay=0,
    ),
    StoryParams(
        treat="honey_buns",
        surface="basket",
        pest="flies",
        response="peppermint_circle",
        hero_name="Rill",
        hero_type="toad",
        friend_name="Lark",
        friend_type="sheep",
        helper_name="Moss Mole",
        helper_type="mole",
        delay=0,
    ),
    StoryParams(
        treat="berry_cakes",
        surface="plate",
        pest="wasps",
        response="broom_only",
        hero_name="Tarn",
        hero_type="fox",
        friend_name="Penny",
        friend_type="hen",
        helper_name="Old Mole Rowan",
        helper_type="mole",
        delay=1,
    ),
    StoryParams(
        treat="plum_tarts",
        surface="basket",
        pest="ants",
        response="broom_only",
        hero_name="Nip",
        hero_type="fox",
        friend_name="Dot",
        friend_type="hen",
        helper_name="Mender Mole",
        helper_type="mole",
        delay=2,
    ),
    StoryParams(
        treat="honey_buns",
        surface="tray",
        pest="wasps",
        response="moon_bell",
        hero_name="Bram",
        hero_type="toad",
        friend_name="Saffy",
        friend_type="sheep",
        helper_name="Master Mole",
        helper_type="mole",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Magic market fable: a plus charm, a smoosh, and a kindly exterminator."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--pest", choices=PESTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the sticky smell lingers before the fix starts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.surface and args.pest:
        treat = TREATS[args.treat]
        surface = SURFACES[args.surface]
        pest = PESTS[args.pest]
        if not hazard_at_risk(treat, surface, pest):
            raise StoryError(explain_rejection(treat, surface, pest))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.surface is None or combo[1] == args.surface)
        and (args.pest is None or combo[2] == args.pest)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, surface_id, pest_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_type = rng.choice(HERO_TYPES)
    friend_type = rng.choice(FRIEND_TYPES)
    hero_name = rng.choice(FOX_NAMES if hero_type == "fox" else ["Pip", "Tarn", "Bram", "Rill"])
    friend_name = rng.choice(HEN_NAMES if friend_type == "hen" else ["Mira", "Lark", "Saffy", "Penny"])
    helper_name = rng.choice(MOLE_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        treat=treat_id,
        surface=surface_id,
        pest=pest_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_name=helper_name,
        helper_type="mole",
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.pest not in PESTS:
        raise StoryError(f"(Unknown pest: {params.pest})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    treat = TREATS[params.treat]
    surface = SURFACES[params.surface]
    pest = PESTS[params.pest]
    response = RESPONSES[params.response]

    if not hazard_at_risk(treat, surface, pest):
        raise StoryError(explain_rejection(treat, surface, pest))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        treat=treat,
        surface=surface,
        pest=pest,
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        sample.to_json()
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treat, surface, pest) combos:\n")
        for treat_id, surface_id, pest_id in combos:
            print(f"  {treat_id:12} {surface_id:8} {pest_id}")
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
            header = f"### {p.hero_name}: {p.treat} on {p.surface} with {p.pest} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
