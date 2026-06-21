#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sport_magazine_transformation_rhyme_inner_monologue_adventure.py
==========================================================================================

A standalone story world about a child on a tiny adventure with a magical sport
magazine. A lost object lands beyond a natural obstacle, a rhyme awakens the
right animal form, and the child crosses safely, then comes home changed on the
inside too.

The domain is intentionally small and constraint-checked:

- a place must actually contain the obstacle,
- the chosen transformation form must truly suit that obstacle,
- explicit invalid requests are rejected with a clear StoryError.

The story uses:
- sport
- magazine
- Transformation
- Rhyme
- Inner Monologue
- Adventure style
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "sister", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "brother", "man"}
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
            "sister": "sister",
            "brother": "brother",
            "friend": "friend",
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
class Setting:
    id: str
    place: str
    afford_obstacles: set[str] = field(default_factory=set)
    opening: str = ""
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
    site: str
    hazard: str
    scene: str
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
class Form:
    id: str
    label: str
    animal: str
    skill: str
    sport_page: str
    body_line: str
    move_line: str
    rhyme_tail: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    ending_image: str
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
class HelperCfg:
    id: str
    type: str
    support: int
    opening: str
    calm_line: str
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


SETTINGS = {
    "park": Setting(
        id="park",
        place="the riverside park",
        afford_obstacles={"creek", "oak_tree"},
        opening="A wind from the water kept turning pages all by itself.",
        tags={"park", "outside"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the windy meadow",
        afford_obstacles={"hill", "oak_tree"},
        opening="Tall grass leaned and whispered like it knew a secret trail.",
        tags={"meadow", "outside"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the old orchard",
        afford_obstacles={"oak_tree", "hill"},
        opening="Rows of trees made green hallways for a small explorer.",
        tags={"orchard", "outside"},
    ),
}

OBSTACLES = {
    "creek": Obstacle(
        id="creek",
        label="creek",
        need="leap",
        site="on the far stepping stone in the middle of the creek",
        hazard="slip into the cold water",
        scene="The creek flashed silver and quick between the stones.",
        tags={"creek", "water"},
    ),
    "oak_tree": Obstacle(
        id="oak_tree",
        label="oak tree",
        need="climb",
        site="high on a bendy branch of the oak tree",
        hazard="scramble up too high and get stuck",
        scene="The old oak tree spread its branches like a gate to the sky.",
        tags={"tree", "climb"},
    ),
    "hill": Obstacle(
        id="hill",
        label="hill",
        need="balance",
        site="beside the little flag at the windy top of the hill",
        hazard="tumble on the loose stones",
        scene="The hill rose steep and stony, with the path curling like a ribbon.",
        tags={"hill", "balance"},
    ),
}

FORMS = {
    "frog": Form(
        id="frog",
        label="frog form",
        animal="frog",
        skill="leap",
        sport_page="a long-jump sport page with bright green borders",
        body_line="knees springy as coiled springs",
        move_line="one neat jump after another",
        rhyme_tail="borrow me jumps both quick and neat",
        tags={"frog", "jump"},
    ),
    "squirrel": Form(
        id="squirrel",
        label="squirrel form",
        animal="squirrel",
        skill="climb",
        sport_page="a climbing sport page with tiny chalky paw prints",
        body_line="fingers light and clever",
        move_line="up the bark in a whir of tail and paws",
        rhyme_tail="borrow me paws with a climbing song",
        tags={"squirrel", "climb"},
    ),
    "goat": Form(
        id="goat",
        label="goat form",
        animal="goat",
        skill="balance",
        sport_page="a mountain-race sport page striped in gold and gray",
        body_line="hooves sure as little drumbeats",
        move_line="from stone to stone without a wobble",
        rhyme_tail="borrow me steps both brave and right",
        tags={"goat", "balance"},
    ),
}

LOST_THINGS = {
    "ribbon": LostThing(
        id="ribbon",
        label="ribbon",
        phrase="the red team ribbon that marked the best hiding place in their game",
        ending_image="The red ribbon fluttered from the stick of the fort like a tiny brave flag.",
        tags={"ribbon"},
    ),
    "whistle": LostThing(
        id="whistle",
        label="whistle",
        phrase="the silver whistle they used to start their pretend races",
        ending_image="The silver whistle rested warm in a small hand instead of dangling alone in the wind.",
        tags={"whistle"},
    ),
    "map": LostThing(
        id="map",
        label="map",
        phrase="the folded treasure map they had tucked inside the magazine",
        ending_image="The folded map lay flat again, ready for another expedition tomorrow.",
        tags={"map"},
    ),
}

HELPERS = {
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        support=2,
        opening="Grandpa had come along with a walking stick and a slow, adventure-ready smile.",
        calm_line="We do brave things with care, not with a rush.",
        cheer="steady and strong",
        tags={"grandparent"},
    ),
    "sister": HelperCfg(
        id="sister",
        type="sister",
        support=1,
        opening="An older sister trotted beside the hero like a scout on watch.",
        calm_line="Pick the page that truly fits the path.",
        cheer="you've got this",
        tags={"sibling"},
    ),
    "friend": HelperCfg(
        id="friend",
        type="friend",
        support=1,
        opening="A best friend hurried along too, eyes wide for any sign of treasure.",
        calm_line="Let's think first and then go.",
        cheer="nice and easy",
        tags={"friend"},
    ),
}


@dataclass
class StoryParams:
    place: str
    obstacle: str
    form: str
    lost_thing: str
    helper: str
    hero_name: str
    hero_gender: str
    helper_name: str
    bravery: int = 5
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_support_steadies(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["worry"] < THRESHOLD:
        return []
    if helper.memes["cheering"] < THRESHOLD:
        return []
    sig = ("steady", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    return []


def _r_matched_form_crosses(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    thing = world.get("thing")
    if hero.meters["transformed"] < THRESHOLD:
        return []
    if not world.facts.get("form_matches", False):
        return []
    sig = ("cross", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["crossed"] += 1
    thing.meters["recovered"] += 1
    hero.memes["wonder"] += 1
    hero.memes["courage"] += 1
    return ["__crossed__"]


CAUSAL_RULES = [
    Rule(name="support_steadies", tag="social", apply=_r_support_steadies),
    Rule(name="matched_form_crosses", tag="physical", apply=_r_matched_form_crosses),
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
        for sent in produced:
            world.say(sent)
    return produced


def form_fits(form: Form, obstacle: Obstacle) -> bool:
    return form.skill == obstacle.need


def place_has_obstacle(setting: Setting, obstacle: Obstacle) -> bool:
    return obstacle.id in setting.afford_obstacles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.afford_obstacles):
            obstacle = OBSTACLES[obstacle_id]
            for form_id, form in FORMS.items():
                if form_fits(form, obstacle):
                    combos.append((place, obstacle_id, form_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    total = params.bravery + helper.support
    return "bold" if total >= 7 else "careful"


def predict_crossing(world: World, form_id: str) -> dict:
    sim = world.copy()
    sim.facts["form_matches"] = form_fits(FORMS[form_id], OBSTACLES[sim.facts["obstacle_cfg"].id])
    sim.get("hero").meters["transformed"] += 1
    propagate(sim, narrate=False)
    return {
        "crossed": sim.get("obstacle").meters["crossed"] >= THRESHOLD,
        "recovered": sim.get("thing").meters["recovered"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, thing: LostThing) -> None:
    world.say(
        f"{hero.id} carried a battered sport magazine under {hero.pronoun('possessive')} arm and marched into {world.setting.place} as if it were the first step of an expedition."
    )
    world.say(world.setting.opening)
    world.say(helper.attrs["opening"])
    world.say(
        f"Inside the magazine was {thing.phrase}, tucked there for safekeeping."
    )


def gust(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, thing: LostThing) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then a rude little gust snapped the pages wide, snatched away {thing.phrase}, and dropped it {obstacle.site}."
    )
    world.say(obstacle.scene)
    world.say(
        f'{hero.id} stopped short. "{obstacle.label.capitalize()}," {hero.pronoun()} whispered.'
    )


def inner_monologue(world: World, hero: Entity, obstacle: Obstacle, helper: Entity) -> None:
    hero.memes["thinking"] += 1
    world.say(
        f'Inside, {hero.pronoun()} thought, "I want to dash after it, but if I guess wrong, I could {obstacle.hazard}. Think, think. The right kind of brave is the kind that notices."'
    )
    world.say(
        f'{helper.id} touched the sport magazine and said, "{helper.attrs["calm_line"]}"'
    )


def choose_page(world: World, hero: Entity, form: Form, obstacle: Obstacle) -> None:
    pred = predict_crossing(world, form.id)
    world.facts["predicted_crossed"] = pred["crossed"]
    world.say(
        f"{hero.id} flipped to {form.sport_page}. In the corner was a rhyme shaped like a trail marker."
    )
    if pred["crossed"]:
        world.say(
            f"{hero.pronoun().capitalize()} knew at once that a {form.animal}'s {form.skill} was exactly what the path demanded."
        )


def cheer(world: World, helper: Entity) -> None:
    helper.memes["cheering"] += 1
    world.say(f'"{helper.attrs["cheer"]}," {helper.id} said.')


def transform(world: World, hero: Entity, form: Form) -> None:
    hero.meters["transformed"] += 1
    hero.attrs["form"] = form.id
    world.say(
        f'{hero.id} read aloud, "Page of sport, page of spring, {form.rhyme_tail}. Let me be small, let me be true, till this brave little job is through."'
    )
    world.say(
        f"At once the world gave a tiny shiver. {hero.id}'s body felt {form.body_line}, and for one bright moment {hero.pronoun()} was in {form.label}."
    )
    propagate(world, narrate=False)


def crossing(world: World, hero: Entity, obstacle: Obstacle, form: Form, thing: LostThing, style: str) -> None:
    if obstacle.meters["crossed"] < THRESHOLD:
        raise StoryError("(Story logic error: the crossing never completed.)")
    if style == "bold":
        world.say(
            f"With a happy gasp, {hero.id} went {form.move_line}, straight toward the prize."
        )
    else:
        world.say(
            f"Slowly and carefully, {hero.id} went {form.move_line}, checking each move before the next one."
        )
    world.say(
        f"In another second, {hero.pronoun()} had reached {thing.label} and tucked it safely close."
    )


def fade_back(world: World, hero: Entity, helper: Entity, thing: LostThing) -> None:
    hero.meters["transformed"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"As soon as {hero.id} turned back toward {helper.id}, the magic gentled and {hero.pronoun()} became a child again, only smiling harder than before."
    )
    world.say(
        f'{hero.id} thought, "I did not become brave because I was magic. The magic worked because I stopped and chose wisely first."'
    )
    world.say(
        f"{helper.id} laughed and wrapped an arm around {hero.pronoun('object')} while {thing.ending_image}"
    )


def close_story(world: World, hero: Entity, thing: LostThing) -> None:
    world.say(
        f"After that, the sport magazine was not just something to read. To {hero.id}, it felt like a folded door into adventures that opened best for patient hearts."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    form: Form,
    thing_cfg: LostThing,
    helper_cfg: HelperCfg,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    helper_name: str = "Grandpa",
    bravery: int = 5,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            attrs={
                "opening": helper_cfg.opening,
                "calm_line": helper_cfg.calm_line,
                "cheer": helper_cfg.cheer,
            },
        )
    )
    obstacle_ent = world.add(
        Entity(id="obstacle", type="obstacle", label=obstacle.label, role="obstacle")
    )
    thing = world.add(
        Entity(id="thing", type="thing", label=thing_cfg.label, role="lost")
    )

    hero.memes["worry"] = 0.0
    hero.memes["courage"] = float(max(0, bravery - 4))
    helper.memes["cheering"] = 0.0
    hero.meters["transformed"] = 0.0
    obstacle_ent.meters["crossed"] = 0.0
    thing.meters["recovered"] = 0.0

    world.facts.update(
        setting=setting,
        obstacle_cfg=obstacle,
        form_cfg=form,
        thing_cfg=thing_cfg,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        obstacle=obstacle_ent,
        thing=thing,
        form_matches=form_fits(form, obstacle),
        bravery=bravery,
        outcome=outcome_of(
            StoryParams(
                place=setting.id,
                obstacle=obstacle.id,
                form=form.id,
                lost_thing=thing_cfg.id,
                helper=helper_cfg.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                helper_name=helper_name,
                bravery=bravery,
            )
        ),
    )

    introduce(world, hero, helper, thing_cfg)
    world.para()
    gust(world, hero, helper, obstacle, thing_cfg)
    inner_monologue(world, hero, obstacle, helper)
    choose_page(world, hero, form, obstacle)
    cheer(world, helper)
    propagate(world, narrate=False)
    world.para()
    transform(world, hero, form)
    crossing(world, hero, obstacle, form, thing_cfg, world.facts["outcome"])
    fade_back(world, hero, helper, thing_cfg)
    world.para()
    close_story(world, hero, thing_cfg)
    return world


KNOWLEDGE = {
    "magazine": [
        (
            "What is a magazine?",
            "A magazine is a booklet with many pages to read and look at. It can have stories, pictures, and facts about things people like.",
        )
    ],
    "sport": [
        (
            "What is a sport?",
            "A sport is a game or activity where people move their bodies and practice a skill. Running, jumping, climbing, and kicking can all be part of sports.",
        )
    ],
    "frog": [
        (
            "Why are frogs good at jumping?",
            "Frogs have strong back legs that push them forward in big hops. Those springy legs help them cross wet places quickly.",
        )
    ],
    "squirrel": [
        (
            "Why can squirrels climb trees so well?",
            "Squirrels have sharp claws and light bodies that help them grip bark. Their tails also help them balance while they climb.",
        )
    ],
    "goat": [
        (
            "Why are goats good on steep places?",
            "Goats are very good at balance. Their feet can stand on small rocky spots without slipping easily.",
        )
    ],
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of moving water. It can be shallow, but the stones beside it may still be slippery.",
        )
    ],
    "tree": [
        (
            "Why should children be careful in tall trees?",
            "Tall trees can be hard to climb down from once you are up high. That is why careful climbing matters.",
        )
    ],
    "hill": [
        (
            "Why can a rocky hill be tricky to cross?",
            "Loose stones can slide under your feet. That makes balance very important on a hill.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike at the end. Rhymes are easy to remember, so people often use them in songs and chants.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "magazine",
    "sport",
    "rhyme",
    "frog",
    "squirrel",
    "goat",
    "creek",
    "tree",
    "hill",
]

GIRL_NAMES = ["Mira", "Lina", "Ava", "Nora", "Zoe", "Tara"]
BOY_NAMES = ["Nico", "Leo", "Max", "Eli", "Finn", "Owen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    form = f["form_cfg"]
    thing = f["thing_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "sport" and "magazine," plus a transformation rhyme.',
        f"Tell a gentle adventure where {hero.id} uses a magical sport magazine, thinks carefully to {hero.pronoun('object')}self, and becomes a {form.animal} long enough to reach a lost {thing.label} beyond a {obstacle.label}.",
        f"Write a story with inner monologue, a spoken rhyme, and a safe magical transformation, where {helper.id} helps {hero.id} choose the right brave move.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    form = f["form_cfg"]
    thing = f["thing_cfg"]
    style = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child explorer, and {helper.id}, who comes along for the adventure. Together they face a small problem in {world.setting.place}.",
        ),
        (
            f"What was inside the sport magazine?",
            f"Inside the sport magazine was {thing.phrase}. It mattered because the wind blew it away and the whole adventure began from that loss.",
        ),
        (
            f"Why did {hero.id} stop to think before moving?",
            f'{hero.id} knew rushing could be a mistake because {hero.pronoun()} might {obstacle.hazard}. So {hero.pronoun()} used an inner thought to slow down and choose the kind of bravery that fits the path.',
        ),
        (
            f"Why did {hero.id} choose the {form.animal} page?",
            f"{hero.pronoun().capitalize()} chose it because a {form.animal}'s {form.skill} matched the problem at the {obstacle.label}. The magic worked well because the form fit the obstacle instead of fighting it.",
        ),
        (
            "What did the rhyme do?",
            f"The rhyme changed {hero.id} into {form.label} for a little while. That gave {hero.pronoun('object')} the right body and movement to reach the lost {thing.label} safely.",
        ),
    ]
    if style == "bold":
        qa.append(
            (
                f"How did {hero.id} cross the {obstacle.label}?",
                f"{hero.pronoun().capitalize()} crossed boldly, moving {form.move_line}. The story shows that boldness came after careful thinking, not before it.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} cross the {obstacle.label}?",
                f"{hero.pronoun().capitalize()} crossed slowly and carefully, moving {form.move_line}. {helper.id}'s calm cheering helped turn worry into steady courage.",
            )
        )
    qa.append(
        (
            f"What changed inside {hero.id} by the end?",
            f'{hero.id} learned that being brave is not the same as rushing. {hero.pronoun().capitalize()} understood that wise choices can make adventure safer and stronger.',
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"magazine", "sport", "rhyme"}
    tags |= set(f["form_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} form_matches={world.facts.get('form_matches')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park",
        obstacle="creek",
        form="frog",
        lost_thing="ribbon",
        helper="grandpa",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Grandpa",
        bravery=5,
    ),
    StoryParams(
        place="orchard",
        obstacle="oak_tree",
        form="squirrel",
        lost_thing="map",
        helper="sister",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Tess",
        bravery=6,
    ),
    StoryParams(
        place="meadow",
        obstacle="hill",
        form="goat",
        lost_thing="whistle",
        helper="friend",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Pip",
        bravery=4,
    ),
]


def explain_rejection(setting: Optional[Setting], obstacle: Obstacle, form: Form) -> str:
    if setting is not None and not place_has_obstacle(setting, obstacle):
        return (
            f"(No story: {setting.place} does not include the needed {obstacle.label} in this world. "
            f"Pick a place that can honestly hold that obstacle.)"
        )
    return (
        f"(No story: {form.label} is built for {form.skill}, but the {obstacle.label} needs {obstacle.need}. "
        f"Choose the animal form that truly fits the path.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny adventure storyworld with a magical sport magazine, a rhyme, and a matching transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--lost-thing", choices=LOST_THINGS, dest="lost_thing")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", dest="helper_name")
    ap.add_argument("--bravery", type=int, choices=list(range(1, 8)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid place/obstacle/form triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        if not place_has_obstacle(setting, obstacle):
            form = FORMS[args.form] if args.form else next(iter(FORMS.values()))
            raise StoryError(explain_rejection(setting, obstacle, form))
    if args.obstacle and args.form:
        obstacle = OBSTACLES[args.obstacle]
        form = FORMS[args.form]
        if not form_fits(form, obstacle):
            setting = SETTINGS[args.place] if args.place else None
            raise StoryError(explain_rejection(setting, obstacle, form))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.form is None or combo[2] == args.form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, form = rng.choice(sorted(combos))
    lost_thing = args.lost_thing or rng.choice(sorted(LOST_THINGS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or {
        "grandpa": "Grandpa",
        "sister": rng.choice(["Tess", "Ruby", "Mina", "June"]),
        "friend": rng.choice(["Pip", "Bo", "Kit", "Lark"]),
    }[helper]
    bravery = args.bravery if args.bravery is not None else rng.randint(3, 7)
    return StoryParams(
        place=place,
        obstacle=obstacle,
        form=form,
        lost_thing=lost_thing,
        helper=helper,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.place]
        obstacle = OBSTACLES[params.obstacle]
        form = FORMS[params.form]
        thing = LOST_THINGS[params.lost_thing]
        helper_cfg = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]}.)") from None

    if not place_has_obstacle(setting, obstacle):
        raise StoryError(explain_rejection(setting, obstacle, form))
    if not form_fits(form, obstacle):
        raise StoryError(explain_rejection(setting, obstacle, form))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        form=form,
        thing_cfg=thing,
        helper_cfg=helper_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        bravery=params.bravery,
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


ASP_RULES = r"""
valid(P,O,F) :- affords(P,O), solves(F,O).

helper_bonus(H,S) :- helper(H), support(H,S).

outcome(bold) :- chosen_helper(H), helper_bonus(H,S), chosen_bravery(B), B + S >= 7.
outcome(careful) :- chosen_helper(H), helper_bonus(H,S), chosen_bravery(B), B + S < 7.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for obstacle_id in sorted(setting.afford_obstacles):
            lines.append(asp.fact("affords", place, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        lines.append(asp.fact("solves", form_id, form.skill == "leap" and "creek" or form.skill == "climb" and "oak_tree" or "hill"))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("support", helper_id, helper.support))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid_combos() matches clingo ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} valid (place, obstacle, form) combos:\n")
        for place, obstacle, form in combos:
            print(f"  {place:8} {obstacle:8} {form}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.form} for {p.obstacle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
