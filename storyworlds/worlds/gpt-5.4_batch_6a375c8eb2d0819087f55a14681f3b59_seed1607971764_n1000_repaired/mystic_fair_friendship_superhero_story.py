#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py
====================================================================

A standalone story world about two friends at a mystic fair who imagine
themselves as superheroes. When something important gets stuck in a tricky
place, one child wants to solve it alone with a flashy move. The friend notices
the risk, predicts what could go wrong, and helps turn the rescue into a real
team effort.

The domain is deliberately small and constraint-checked:
- each target item is stuck in a particular kind of place
- each rescue method only works for some place types
- low-common-sense methods are known to the world but refused
- every generated story resolves with friendship as the real superpower

Run it
------
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py --theme moon_guard --target pond_lantern
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py --method superhero_jump
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mystic_fair_friendship_superhero_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Theme:
    id: str
    opening: str
    hero_call: str
    mission_word: str
    closing: str
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
class Target:
    id: str
    item: str
    owner_role: str
    owner_desc: str
    place: str
    need: str
    sight: str
    attempt: str
    danger: str
    solved_image: str
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
    covers: set[str]
    tool: str
    helper: str
    teamwork_text: str
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


def _r_wobble(world: World) -> list[str]:
    hero = world.get("hero")
    target = world.get("target")
    if hero.meters["solo_attempt"] < THRESHOLD or target.meters["stuck"] < THRESHOLD:
        return []
    sig = ("wobble", world.facts["target_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("fair").meters["risk"] += 1
    hero.memes["alarm"] += 1
    world.get("friend").memes["worry"] += 1
    return ["__wobble__"]


def _r_recovered(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["secured"] < THRESHOLD:
        return []
    sig = ("recovered", world.facts["target_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    hero = world.get("hero")
    friend = world.get("friend")
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.get("fair").memes["cheer"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="risk", apply=_r_wobble),
    Rule(name="recovered", tag="resolution", apply=_r_recovered),
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


def target_at_risk(target: Target, method: Method) -> bool:
    return target.need in method.covers


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for target_id, target in TARGETS.items():
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and target_at_risk(target, method):
                    combos.append((theme_id, target_id, method_id))
    return combos


def explain_target_method(target: Target, method: Method) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it is too showy or unsafe for this world "
            f"(sense={method.sense} < {SENSE_MIN}). Try a steadier rescue such as {better}.)"
        )
    return (
        f"(No story: {method.tool} cannot sensibly reach {target.item} at {target.place}. "
        f"Pick a method that handles a {target.need} rescue.)"
    )


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["solo_attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("fair").meters["risk"],
        "friend_worry": sim.get("friend").memes["worry"],
    }


def introduce(world: World, theme: Theme, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} hurried into the mystic fair with "
        f"paper capes fluttering behind them. {theme.opening}"
    )
    world.say(
        f'"{theme.hero_call}!" {hero.id} cried. "{theme.mission_word} mission!" '
        f'{friend.id} bumped {hero.pronoun("possessive")} shoulder and laughed, because '
        f"their friendship always made the game feel bigger."
    )


def discover_problem(world: World, target_cfg: Target, owner: Entity) -> None:
    target = world.get("target")
    target.meters["stuck"] = 1.0
    world.say(
        f"Near the middle of the fair, {owner.id}, {target_cfg.owner_desc}, gasped. "
        f'{target_cfg.sight}'
    )
    world.say(
        f"{owner.id} looked so close to tears that the whole moment suddenly felt like a real rescue."
    )


def boast(world: World, hero: Entity, target_cfg: Target) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"I can fix it in one super move," {hero.id} said, already getting ready to {target_cfg.attempt}.'
    )


def warn(world: World, friend: Entity, hero: Entity, target_cfg: Target) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_risk"] = pred["risk"]
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} caught {hero.pronoun("possessive")} cape. "Wait," {friend.pronoun()} said. '
        f'"If you try that alone, {target_cfg.danger}."'
    )
    if pred["risk"] >= THRESHOLD:
        world.say(
            f'{friend.id} was not trying to spoil the fun. {friend.pronoun().capitalize()} could already picture the trouble before it happened.'
        )


def solo_attempt(world: World, hero: Entity, target_cfg: Target) -> None:
    hero.meters["solo_attempt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took one quick step to {target_cfg.attempt}, and at once the danger became real."
    )
    if world.get("fair").meters["risk"] >= THRESHOLD:
        world.say(target_cfg.danger)


def rethink(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} stopped. For one tiny second, {hero.pronoun()} looked embarrassed, but then "
        f"{hero.pronoun()} nodded. A real hero could listen to a friend."
    )


def teamwork_rescue(world: World, hero: Entity, friend: Entity, owner: Entity, method: Method, target_cfg: Target) -> None:
    target = world.get("target")
    world.say(
        f"Together they asked {method.helper} for {method.tool}. {method.teamwork_text}"
    )
    target.meters["secured"] += 1
    propagate(world, narrate=False)
    world.say(method.success_text.replace("{item}", target_cfg.item))
    world.say(
        f"{owner.id} hugged {target_cfg.item} to {owner.pronoun('possessive')} chest, and the nearby grown-ups clapped."
    )


def ending(world: World, theme: Theme, hero: Entity, friend: Entity, owner: Entity) -> None:
    world.say(
        f'"You two were better than any flying punch," {owner.id} said. "You rescued it together."'
    )
    world.say(
        f"{hero.id} grinned at {friend.id}. The mystic fair lights shimmered on their capes, and both friends knew their best superpower was friendship."
    )
    world.say(theme.closing)


def tell(
    theme: Theme,
    target_cfg: Target,
    method: Method,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    friend_name: str = "Kai",
    friend_gender: str = "boy",
    owner_name: str = "Pip",
    owner_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["bold"],
            attrs={"cape": "paper cape"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["steady"],
            attrs={"cape": "paper cape"},
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            traits=["small"],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    fair = world.add(
        Entity(
            id="fair",
            kind="thing",
            type="place",
            label="mystic fair",
        )
    )
    target = world.add(
        Entity(
            id="target",
            kind="thing",
            type="item",
            label=target_cfg.item,
        )
    )

    world.facts.update(
        theme=theme,
        target_cfg=target_cfg,
        method=method,
        hero=hero,
        friend=friend,
        owner=owner,
        parent=parent,
        rescued=False,
        predicted_risk=0.0,
    )

    introduce(world, theme, hero, friend)
    discover_problem(world, target_cfg, owner)

    world.para()
    boast(world, hero, target_cfg)
    warn(world, friend, hero, target_cfg)
    solo_attempt(world, hero, target_cfg)
    rethink(world, hero, friend)

    world.para()
    teamwork_rescue(world, hero, friend, owner, method, target_cfg)
    ending(world, theme, hero, friend, owner)

    world.facts["rescued"] = target.meters["secured"] >= THRESHOLD
    return world


THEMES = {
    "moon_guard": Theme(
        id="moon_guard",
        opening="Silver streamers curled above every booth, and a moon-painted drum rolled out a brave parade beat.",
        hero_call="Moon Guard, to the sky",
        mission_word="Moon Guard",
        closing="Then they ran off toward the next sparkling booth, not as lone champions, but as a team.",
        tags={"fair", "friendship", "superhero"},
    ),
    "comet_watch": Theme(
        id="comet_watch",
        opening="A comet banner snapped over the game tents, and the air smelled like cinnamon apples and warm sugar.",
        hero_call="Comet Watch, zoom",
        mission_word="Comet Watch",
        closing="The fair seemed even bigger after that, as if teamwork had made room for more light.",
        tags={"fair", "friendship", "superhero"},
    ),
    "star_shield": Theme(
        id="star_shield",
        opening="Gold stars spun on strings above the lanes, and every lantern looked as if it had learned a little magic.",
        hero_call="Star Shield heroes, ready",
        mission_word="Star Shield",
        closing="Side by side, they strode on through the music, their capes fluttering like one happy flag.",
        tags={"fair", "friendship", "superhero"},
    ),
}

TARGETS = {
    "tree_mask": Target(
        id="tree_mask",
        item="the parade mask",
        owner_role="performer",
        owner_desc="a little parade dancer in silver shoes",
        place="the apple tree branch",
        need="high",
        sight="A gust had carried the parade mask up into an apple tree branch just above the ribbon booth.",
        attempt="climb the booth rail and grab it",
        danger="The painted rail gave a shaky wobble, and one slip would have sent the whole rescue crashing into the booth.",
        solved_image="the mask shining safely in small hands again",
        tags={"high", "mask", "fair"},
    ),
    "pond_lantern": Target(
        id="pond_lantern",
        item="the moon lantern",
        owner_role="child",
        owner_desc="a younger child with a paper moon badge",
        place="the duck pond",
        need="water",
        sight="A glowing moon lantern had drifted away and was bobbing just past the edge of the duck pond.",
        attempt="lean far over the pond wall and snatch it",
        danger="The mossy stones were slick, and one more inch would have meant a splash into the cold green water.",
        solved_image="the moon lantern glowing warm and dry again",
        tags={"water", "lantern", "fair"},
    ),
    "wagon_emblem": Target(
        id="wagon_emblem",
        item="the hero emblem",
        owner_role="vendor",
        owner_desc="the tiny helper from the badge cart",
        place="under the parade wagon",
        need="narrow",
        sight="The hero emblem from the badge cart had skittered under the parade wagon where no hand could reach safely.",
        attempt="crawl under the wheel frame alone",
        danger="The wagon wheels creaked, and there was barely room to squeeze in without bumping something heavy.",
        solved_image="the hero emblem bright on the badge cart once more",
        tags={"narrow", "badge", "fair"},
    ),
}

METHODS = {
    "hook_pole": Method(
        id="hook_pole",
        sense=3,
        covers={"high"},
        tool="a long velvet hook pole",
        helper="the ribbon seller",
        teamwork_text="While one friend steadied the pole, the other guided the hook slowly upward until the mask ribbon slipped free.",
        success_text="Down came {item}, swinging like a rescued treasure from the sky.",
        qa_text="They borrowed a long hook pole and worked together to lift the item down from above.",
        tags={"pole", "teamwork", "high"},
    ),
    "pond_net": Method(
        id="pond_net",
        sense=3,
        covers={"water"},
        tool="a wide pond net with a bamboo handle",
        helper="the pond keeper",
        teamwork_text="One friend lay flat and held the other by the waist while the net skimmed softly across the water.",
        success_text="With one gentle scoop, {item} rose out of the pond without getting dunked.",
        qa_text="They used a wide pond net, and one friend kept the other safe while they scooped the item out.",
        tags={"net", "teamwork", "water"},
    ),
    "grabber_claw": Method(
        id="grabber_claw",
        sense=3,
        covers={"narrow"},
        tool="a grabber claw from the repair cart",
        helper="the wheel fixer",
        teamwork_text="Kneeling shoulder to shoulder, they aimed the claw together, one guiding the handle and the other watching the tiny pinchers.",
        success_text="The claw clicked shut on {item} and slid it out from the shadows.",
        qa_text="They used a grabber claw together so nobody had to crawl into the tight space.",
        tags={"claw", "teamwork", "narrow"},
    ),
    "superhero_jump": Method(
        id="superhero_jump",
        sense=1,
        covers={"high"},
        tool="a flying leap",
        helper="nobody at all",
        teamwork_text="It relied on a wild jump instead of a steady plan.",
        success_text="{item} nearly came loose, but the move was far too risky to belong in this world.",
        qa_text="It was a flashy jump, not a safe rescue.",
        tags={"jump", "unsafe"},
    ),
    "reach_by_hand": Method(
        id="reach_by_hand",
        sense=1,
        covers={"water", "narrow"},
        tool="bare hands stretched too far",
        helper="nobody at all",
        teamwork_text="It asked one child to get dangerously close instead of making a safe team plan.",
        success_text="{item} stayed out of reach, and the danger only grew.",
        qa_text="It was an unsafe reach, not a proper rescue.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nova", "Lina", "Ruby", "Tess", "Mira", "Skye", "Ivy", "Ada"]
BOY_NAMES = ["Kai", "Finn", "Leo", "Milo", "Jax", "Owen", "Nico", "Zane"]


@dataclass
class StoryParams:
    theme: str = "moon_guard"
    target: str = "tree_mask"
    method: str = "hook_pole"
    hero_name: str = "Nova"
    hero_gender: str = "girl"
    friend_name: str = "Kai"
    friend_gender: str = "boy"
    owner_name: str = "Pip"
    owner_gender: str = "girl"
    parent: str = "mother"
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
    "fair": [
        (
            "What is a fair?",
            "A fair is a place with booths, games, lights, and treats where many people come to have fun together."
        )
    ],
    "friendship": [
        (
            "Why can friendship feel like a superpower?",
            "A good friend helps you notice danger, share brave jobs, and keep going when you feel stuck. Working together often solves problems better than showing off alone."
        )
    ],
    "pole": [
        (
            "What is a hook pole used for?",
            "A hook pole is a long stick with a curved end that can catch or lift something high up. It helps people reach safely without climbing."
        )
    ],
    "net": [
        (
            "What does a pond net do?",
            "A pond net lets you scoop something from water without leaning in too far. The long handle helps you stay safer."
        )
    ],
    "claw": [
        (
            "What is a grabber claw?",
            "A grabber claw is a tool that pinches and picks up something from a tight place. It helps you reach where hands do not fit well."
        )
    ],
    "high": [
        (
            "Why is climbing somewhere shaky a bad idea?",
            "If something wobbles under your feet, you can slip before you are ready. A safer tool is better than a rushed climb."
        )
    ],
    "water": [
        (
            "Why should children be careful near a pond edge?",
            "Pond edges can be slippery, and a child can lose balance quickly there. Staying low and having help keeps the body steadier."
        )
    ],
    "narrow": [
        (
            "Why can tight spaces under wagons or carts be unsafe?",
            "Tight spaces can pinch you or make it hard to move back out. Heavy wheels and hard boards also leave very little room for mistakes."
        )
    ],
}
KNOWLEDGE_ORDER = ["fair", "friendship", "high", "water", "narrow", "pole", "net", "claw"]


def generation_prompts(world: World) -> list[str]:
    theme = world.facts["theme"]
    target = world.facts["target_cfg"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write a superhero story for a 3-to-5-year-old set at a mystic fair where friendship helps solve a rescue. Include the words "mystic" and "fair".',
        f"Tell a gentle story where {hero.id} wants to make a flashy solo rescue, but {friend.id} helps turn the problem into teamwork.",
        f"Write a story about two child heroes at a fair rescuing {target.item} and learning that friendship is a stronger power than showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    owner = world.facts["owner"]
    target = world.facts["target_cfg"]
    method = world.facts["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two friends pretending to be superheroes at a mystic fair. It is also about {owner.id}, who needed help when {target.item} got stuck."
        ),
        (
            f"What problem did they find at the fair?",
            f"They found that {target.item} was stuck at {target.place}. That mattered because it belonged to {owner.id}, and the lost item turned their game into a real rescue."
        ),
        (
            f"Why did {friend.id} stop {hero.id} from going alone?",
            f"{friend.id} saw that trying to {target.attempt} would be risky. In the story world, the danger was clear because {target.danger.lower()}"
        ),
        (
            "How did they solve the problem?",
            f"{method.qa_text} That made the rescue safer because each friend handled part of the job instead of one child trying a risky stunt alone."
        ),
        (
            "What did the children learn?",
            f"They learned that friendship was their best superpower. The ending proves it because the rescue works only after they listen, trust each other, and act as a team."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fair", "friendship"} | set(world.facts["target_cfg"].tags) | set(world.facts["method"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon_guard",
        target="tree_mask",
        method="hook_pole",
        hero_name="Nova",
        hero_gender="girl",
        friend_name="Kai",
        friend_gender="boy",
        owner_name="Pip",
        owner_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="comet_watch",
        target="pond_lantern",
        method="pond_net",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        owner_name="Lulu",
        owner_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="star_shield",
        target="wagon_emblem",
        method="grabber_claw",
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        owner_name="Toby",
        owner_gender="boy",
        parent="mother",
    ),
]


ASP_RULES = r"""
sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
compatible(Tg, M) :- target(Tg), method(M), needs(Tg, N), covers(M, N), sensible(M).
valid(Th, Tg, M) :- theme(Th), compatible(Tg, M).

rescued(Tg, M) :- compatible(Tg, M).
#show valid/3.
#show rescued/2.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("needs", target_id, target.need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for cover in sorted(method.covers):
            lines.append(asp.fact("covers", method_id, cover))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_rescued_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "rescued")))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sensible)} clingo={sorted(asp_sense)}")

    py_rescued = {(target_id, method_id) for (_, target_id, method_id) in valid_combos()}
    asp_pairs = set(asp_rescued_pairs())
    if py_rescued == asp_pairs:
        print(f"OK: rescued pair model matches ({len(py_rescued)} target/method pairs).")
    else:
        rc = 1
        print("MISMATCH in rescued target/method pairs.")
        if py_rescued - asp_pairs:
            print("  only in python:", sorted(py_rescued - asp_pairs))
        if asp_pairs - py_rescued:
            print("  only in clingo:", sorted(asp_pairs - py_rescued))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a mystic fair superhero rescue where friendship is the real power."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--target", choices=sorted(TARGETS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method is not None:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_target_method(TARGETS[args.target] if args.target else next(iter(TARGETS.values())), method))

    if args.target is not None and args.method is not None:
        target = TARGETS[args.target]
        method = METHODS[args.method]
        if not target_at_risk(target, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_target_method(target, method))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.target is None or combo[1] == args.target)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, target_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    owner_gender = rng.choice(["girl", "boy"])
    owner_name = _pick_name(rng, owner_gender, avoid=hero_name if hero_name != friend_name else "")
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        theme=theme_id,
        target=target_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    theme = THEMES[params.theme]
    target = TARGETS[params.target]
    method = METHODS[params.method]

    if method.sense < SENSE_MIN:
        raise StoryError(explain_target_method(target, method))
    if not target_at_risk(target, method):
        raise StoryError(explain_target_method(target, method))

    world = tell(
        theme=theme,
        target_cfg=target,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        parent_type=params.parent,
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
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, target, method) combos:\n")
        for theme_id, target_id, method_id in combos:
            print(f"  {theme_id:12} {target_id:13} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.friend_name}: {p.target} with {p.method} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
