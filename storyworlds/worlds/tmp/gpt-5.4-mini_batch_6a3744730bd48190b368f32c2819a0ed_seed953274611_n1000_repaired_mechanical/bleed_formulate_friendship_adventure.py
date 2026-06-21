#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bleed_formulate_friendship_adventure.py
=======================================================================

A standalone storyworld about an adventurous friendship:
two pals go on a small quest, one gets a scrape that makes them bleed,
and together they formulate a careful plan that turns the trip into a safe,
brave ending.

The world keeps the prose driven by state:
- typed entities with physical meters and emotional memes,
- a small causal engine,
- a reasonableness gate,
- three Q&A sets grounded in the simulated world,
- and an inline ASP twin for parity checks.

Seed words: bleed, formulate
Feature: Friendship
Style: Adventure
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
BRAVE_START = 5.0
CALM_TRAITS = {"careful", "thoughtful", "steady", "smart", "kind"}


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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Setting:
    id: str
    place: str
    detail: str
    route: str
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
class Quest:
    id: str
    goal: str
    treasure: str
    clue: str
    path: str
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
class Hazard:
    id: str
    label: str
    surface: str
    makes_bleed: bool = False
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
    phrase: str
    use: str
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
class Plan:
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


@dataclass
class StoryParams:
    setting: str
    quest: str
    hazard: str
    aid: str
    plan: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    friend_age: int = 6
    relation: str = "friends"
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
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


def _r_bleed(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["bleeding"] < THRESHOLD:
            continue
        sig = ("bleed", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["alarm"] += 1
        for c in world.characters():
            if c.id != e.id:
                c.memes["worry"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("bleed", _r_bleed)]


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


def hazard_at_risk(hazard: Hazard, quest: Quest) -> bool:
    return hazard.makes_bleed and "trail" in quest.tags


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= 2]


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.sense)


def bleed_severity(delay: int) -> int:
    return 1 + delay


def is_safe(plan: Plan, delay: int) -> bool:
    return plan.power >= bleed_severity(delay)


def predict_bleed(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _trigger_hazard(sim, sim.get(hazard_id), narrate=False)
    return {
        "bleeding": sim.get("hero").meters["bleeding"] >= THRESHOLD,
        "alarm": sim.get("friend").memes["worry"] >= THRESHOLD,
    }


def _trigger_hazard(world: World, hazard: Entity, narrate: bool = True) -> None:
    hazard.meters["touched"] += 1
    hazard.meters["sharp"] += 1
    world.get("hero").meters["bleeding"] += 1
    propagate(world, narrate=narrate)


def open_adventure(world: World, hero: Entity, friend: Entity, setting: Setting, quest: Quest) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright morning, {hero.id} and {friend.id} set out for {setting.place}. "
        f"{setting.detail} {quest.route}"
    )
    world.say(
        f'"{quest.goal}!" {hero.id} said. "{quest.clue}" {friend.id} answered, and the two friends grinned.'
    )


def search(world: World, hero: Entity, friend: Entity, quest: Quest, setting: Setting) -> None:
    world.para()
    world.say(
        f"They followed the {setting.route} and looked for {quest.treasure}. "
        f"{quest.path}"
    )
    hero.memes["brave"] += 1
    friend.memes["brave"] += 1


def slip(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["startle"] += 1
    world.say(
        f"Then {hero.id} stepped on {hazard.surface}, slipped, and {hazard.label} made {hero.pronoun('object')} bleed."
    )
    world.say(f"{friend.id} gasped and ran closer.")


def formulate(world: World, friend: Entity, adult: Entity, aid: Aid, plan: Plan) -> None:
    friend.memes["thoughtful"] += 1
    world.say(
        f'"We have to formulate a plan," {friend.id} said. "{adult.label_word.capitalize()} can help, and we have {aid.phrase}."'
    )
    world.say(
        f'{adult.label_word.capitalize()} nodded and used {aid.use}. {plan.text}.'
    )


def rescue_fail(world: World, adult: Entity, plan: Plan, hazard: Hazard) -> None:
    world.say(
        f"{adult.label_word.capitalize()} tried, but {plan.fail}."
    )
    world.say(
        f"The scrape kept stinging, and the path felt far too risky to keep walking."
    )


def finish_story(world: World, hero: Entity, friend: Entity, adult: Entity, aid: Aid, setting: Setting) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"At last, {adult.label_word} wrapped the scrape, and {hero.id} held {aid.label} close while the friends finished their adventure."
    )
    world.say(
        f"They walked home together under {setting.place}'s open sky, proud, careful, and still best friends."
    )


def grim_finish(world: World, hero: Entity, friend: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"{adult.label_word.capitalize()} led them home, and the map went back in the bag."
    )
    world.say(
        f"Even so, {hero.id} and {friend.id} stayed side by side, because friendship mattered more than any lost treasure."
    )


SETTING_REGISTRY = {
    "harbor": Setting(
        id="harbor",
        place="the harbor path",
        detail="The docks stood ahead like a tiny kingdom of ropes and wood.",
        route="The gulls pointed the way.",
    ),
    "forest": Setting(
        id="forest",
        place="the forest trail",
        detail="Tall trees made a green tunnel, and the leaves hissed softly overhead.",
        route="A mossy trail wound between the roots.",
    ),
    "canyon": Setting(
        id="canyon",
        place="the canyon walk",
        detail="Red rocks glowed in the sun, and the wind whispered through the stone.",
        route="A narrow path curved beside the cliffs.",
    ),
}

QUEST_REGISTRY = {
    "map": Quest(
        id="map",
        goal="Let's find the hidden chest!",
        treasure="the hidden chest",
        clue="We just need to follow the map.",
        path="A red X marked a bend near the trail.",
        tags={"trail", "map"},
    ),
    "cave": Quest(
        id="cave",
        goal="Let's find the cave lantern!",
        treasure="the cave lantern",
        clue="The old sign says it is close.",
        path="A dark opening waited behind the rocks.",
        tags={"trail", "cave"},
    ),
    "island": Quest(
        id="island",
        goal="Let's find the island flag!",
        treasure="the island flag",
        clue="The compass says the prize is nearby.",
        path="A windy turn led toward the water.",
        tags={"trail", "sea"},
    ),
}

HAZARD_REGISTRY = {
    "thorn": Hazard(
        id="thorn",
        label="a thorn bush",
        surface="a thorny vine",
        makes_bleed=True,
        tags={"thorn", "trail"},
    ),
    "shell": Hazard(
        id="shell",
        label="a sharp shell",
        surface="a sharp shell",
        makes_bleed=True,
        tags={"shell", "trail"},
    ),
    "stone": Hazard(
        id="stone",
        label="a rough stone",
        surface="a rough stone",
        makes_bleed=True,
        tags={"stone", "trail"},
    ),
}

AID_REGISTRY = {
    "bandage": Aid(
        id="bandage",
        label="bandage",
        phrase="a small bandage",
        use="opened the bandage pack",
        tags={"aid"},
    ),
    "water": Aid(
        id="water",
        label="water bottle",
        phrase="a clean water bottle",
        use="washed the scrape with clean water",
        tags={"aid"},
    ),
    "cloth": Aid(
        id="cloth",
        label="clean cloth",
        phrase="a clean cloth",
        use="pressed the cloth gently over the cut",
        tags={"aid"},
    ),
}

PLANS = {
    "bandage": Plan(
        id="bandage",
        sense=3,
        power=3,
        text="They cleaned the scrape and covered it with a bandage",
        fail="the bandage was too small and the blood kept coming",
        qa_text="cleaned the scrape and covered it with a bandage",
        tags={"aid"},
    ),
    "water_cloth": Plan(
        id="water_cloth",
        sense=3,
        power=3,
        text="They washed the scrape with clean water and pressed it with a cloth",
        fail="the cloth slipped and the scrape stayed open",
        qa_text="washed the scrape with clean water and pressed it with a cloth",
        tags={"aid"},
    ),
    "rush_home": Plan(
        id="rush_home",
        sense=2,
        power=2,
        text="They hurried home and got help right away",
        fail="the path was too long, and the bleeding got worse before help came",
        qa_text="hurried home and got help right away",
        tags={"aid"},
    ),
    "stomp": Plan(
        id="stomp",
        sense=1,
        power=1,
        text="They stomped the ground and hoped the scrape would stop",
        fail="stomping did not help at all",
        qa_text="stomped the ground and hoped the scrape would stop",
        tags={"aid"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ava", "Zoe", "Elin"]
BOY_NAMES = ["Toby", "Finn", "Jace", "Milo", "Eli", "Noah"]
TRAITS = ["careful", "thoughtful", "steady", "kind", "smart", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTING_REGISTRY.items():
        for qid, quest in QUEST_REGISTRY.items():
            if "trail" not in quest.tags:
                continue
            for hid in HAZARD_REGISTRY:
                if hazard_at_risk(HAZARD_REGISTRY[hid], quest):
                    combos.append((sid, qid, hid))
    return combos


def explain_rejection(hazard: Hazard, quest: Quest) -> str:
    return (
        f"(No story: {hazard.label} would not fit this adventure well, or it would not create a clear bleed problem on {quest.treasure}. "
        f"Pick a trail quest and a sharp hazard.)"
    )


def explain_plan(pid: str) -> str:
    p = PLANS[pid]
    better = ", ".join(sorted(x.id for x in sensible_plans()))
    return (
        f"(Refusing plan '{pid}': it is too weak for this storyworld's common sense gate. "
        f"Try one of: {better}.)"
    )


def tell(setting: Setting, quest: Quest, hazard: Hazard, aid: Aid, plan: Plan,
         hero: str = "Lina", hero_gender: str = "girl",
         friend: str = "Pip", friend_gender: str = "boy",
         adult: str = "mother", trait: str = "careful",
         delay: int = 0, hero_age: int = 6, friend_age: int = 6,
         relation: str = "friends") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero", traits=[trait]))
    f = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend", traits=["brave"]))
    a = world.add(Entity(id="Adult", kind="character", type=adult, role="adult", label="the grown-up"))
    world.add(Entity(id="scrape", type="scrape", label=hazard.label))

    h.memes["bravery"] = BRAVE_START
    f.memes["bravery"] = BRAVE_START
    world.facts["relation"] = relation

    open_adventure(world, h, f, setting, quest)
    search(world, h, f, quest, setting)
    world.para()
    slip(world, h, hazard)
    if predict_bleed(world, "scrape")["bleeding"]:
        formulate(world, f, a, aid, plan)
    else:
        world.say("Nothing went wrong, so they kept walking and never needed a rescue.")

    if is_safe(plan, delay):
        world.para()
        world.get("scrape").meters["bleeding"] = 0.0
        world.get("scrape").memes["calm"] += 1
        finish_story(world, h, f, a, aid, setting)
        outcome = "safe"
    else:
        world.para()
        rescue_fail(world, a, plan, hazard)
        grim_finish(world, h, f, a, setting)
        outcome = "unsafe"

    world.facts.update(
        hero=h, friend=f, adult=a, setting=setting, quest=quest, hazard=hazard,
        aid=aid, plan=plan, delay=delay, outcome=outcome, bleeding=True,
        solved=outcome == "safe",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old about friendship that includes the words "bleed" and "formulate".',
        f"Tell a small adventure where {f['hero'].id} and {f['friend'].id} go on a quest, one gets hurt and starts to bleed, and the friends formulate a careful plan together.",
        f"Write a gentle friendship adventure with a brave child, a worried friend, and a grown-up helper who solves the problem safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    quest = f["quest"]
    hazard = f["hazard"]
    aid = f["aid"]
    plan = f["plan"]
    out: list[QAItem] = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {friend.id} went together as friends, with {adult.label_word} nearby to help if needed.",
        ),
        QAItem(
            question="What made the story turn scary?",
            answer=f"{hero.id} stepped on {hazard.label}, and the scrape started to bleed. That turned the quest from playful to careful in a moment.",
        ),
        QAItem(
            question="What did the friends do next?",
            answer=f"{friend.id} helped formulate a plan with {adult.label_word}. They used {aid.phrase} and chose a safe way to handle the scrape.",
        ),
    ]
    if f["outcome"] == "safe":
        out.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended safely, with the scrape cleaned and covered. {hero.id} and {friend.id} kept their friendship strong and finished the adventure together.",
            )
        )
        out.append(
            QAItem(
                question="Why was the plan a good one?",
                answer=f"The plan worked because it was careful and strong enough for the scrape. It stopped the bleeding and let the friends keep going without panic.",
            )
        )
    else:
        out.append(
            QAItem(
                question="How did the grown-up help?",
                answer=f"{adult.label_word.capitalize()} tried to help, but the plan was too weak for the scrape. The friends had to head home, still together, but with the adventure cut short.",
            )
        )
    return out


KNOWLEDGE = {
    "bleed": [(
        "What does it mean to bleed?",
        "To bleed means that blood comes out of a cut or scrape. It can happen when skin gets hurt.",
    )],
    "formulate": [(
        "What does it mean to formulate a plan?",
        "To formulate a plan means to think carefully and make a plan step by step. It is a smart way to solve a problem.",
    )],
    "friendship": [(
        "What is friendship?",
        "Friendship means caring about someone, helping them, and having fun together. Good friends stay kind to each other.",
    )],
    "adventure": [(
        "What is an adventure?",
        "An adventure is a trip or story where something exciting happens. Adventures often have a goal, a surprise, and a happy ending.",
    )],
    "bandage": [(
        "What is a bandage for?",
        "A bandage covers a small cut or scrape so it can stay clean while it heals.",
    )],
    "water": [(
        "Why do people use clean water on a scrape?",
        "Clean water helps wash dirt away from a cut or scrape. That makes the skin cleaner and safer.",
    )],
    "thorn": [(
        "Why can a thorn bush be dangerous?",
        "Thorns are sharp, so they can scratch skin and make it bleed. That is why you should be careful near them.",
    )],
    "shell": [(
        "Why can a sharp shell be dangerous?",
        "A sharp shell can cut skin if you step on it or grab it the wrong way. Sharp things can make a scrape bleed.",
    )],
    "stone": [(
        "Why can a rough stone be dangerous?",
        "A rough stone can trip you or scratch you if you fall on it. Scratches can hurt and sometimes bleed a little.",
    )],
}
KNOWLEDGE_ORDER = ["adventure", "friendship", "bleed", "formulate", "bandage", "water", "thorn", "shell", "stone"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"adventure", "friendship", "bleed", "formulate"}
    tags |= set(world.facts["hazard"].tags)
    tags |= set(world.facts["aid"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="forest", quest="map", hazard="thorn", aid="bandage", plan="bandage",
        hero="Lina", hero_gender="girl", friend="Pip", friend_gender="boy",
        adult="mother", trait="careful", delay=0, hero_age=6, friend_age=6, relation="friends",
    ),
    StoryParams(
        setting="harbor", quest="cave", hazard="shell", aid="water", plan="water_cloth",
        hero="Milo", hero_gender="boy", friend="Nia", friend_gender="girl",
        adult="father", trait="thoughtful", delay=0, hero_age=6, friend_age=6, relation="friends",
    ),
    StoryParams(
        setting="canyon", quest="island", hazard="stone", aid="cloth", plan="rush_home",
        hero="Ava", hero_gender="girl", friend="Noah", friend_gender="boy",
        adult="mother", trait="steady", delay=1, hero_age=6, friend_age=6, relation="friends",
    ),
]


def explain_response(pid: str) -> str:
    return explain_plan(pid)


def outcome_of(params: StoryParams) -> str:
    return "safe" if is_safe(PLANS[params.plan], params.delay) else "unsafe"


ASP_RULES = r"""
hazard(F, Q) :- makes_bleed(F), trail(Q).
sensible(P) :- plan(P), sense(P, S), min_sense(M), S >= M.
safe(P, D) :- power(P, Pow), severity(D, Sev), Pow >= Sev.
severity(D, Sev) :- delay(D), Sev = D + 1.
outcome(safe) :- sensible(P), safe(P, D).
outcome(unsafe) :- sensible(P), not safe(P, D), delay(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUEST_REGISTRY.items():
        lines.append(asp.fact("quest", qid))
        if "trail" in q.tags:
            lines.append(asp.fact("trail", qid))
    for hid, h in HAZARD_REGISTRY.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_bleed:
            lines.append(asp.fact("makes_bleed", hid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
        lines.append(asp.fact("power", pid, p.power))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate")
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            sample = generate(CURATED[0])
            emit(sample)
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        if not sample.story.strip():
            rc = 1
            print("SMOKE TEST FAILED: empty story")
    if rc == 0:
        print("OK: ASP parity and generate/emit smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Friendship adventure storyworld with a bleed-and-formulate beat.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--hazard", choices=HAZARD_REGISTRY)
    ap.add_argument("--aid", choices=AID_REGISTRY)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait", choices=sorted(CALM_TRAITS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.plan not in PLANS:
        raise StoryError("Unknown plan.")
    if args.hazard and args.quest:
        hz = HAZARD_REGISTRY[args.hazard]
        qs = QUEST_REGISTRY[args.quest]
        if not hazard_at_risk(hz, qs):
            raise StoryError(explain_rejection(hz, qs))
    if args.plan and PLANS[args.plan].sense < 2:
        raise StoryError(explain_plan(args.plan))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.quest is None or c[1] == args.quest)
        and (args.hazard is None or c[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, quest, hazard = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AID_REGISTRY))
    plan = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    g1 = args.hero_gender or rng.choice(["girl", "boy"])
    g2 = args.friend_gender or ("boy" if g1 == "girl" else "girl")
    hero = args.hero or _pick_name(rng, g1)
    friend = args.friend or _pick_name(rng, g2, avoid=hero)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(sorted(CALM_TRAITS))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting, quest=quest, hazard=hazard, aid=aid, plan=plan,
        hero=hero, hero_gender=g1, friend=friend, friend_gender=g2,
        adult=adult, trait=trait, delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    for key, reg in [("setting", SETTING_REGISTRY), ("quest", QUEST_REGISTRY), ("hazard", HAZARD_REGISTRY), ("aid", AID_REGISTRY), ("plan", PLANS)]:
        if getattr(params, key) not in reg:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTING_REGISTRY[params.setting],
        QUEST_REGISTRY[params.quest],
        HAZARD_REGISTRY[params.hazard],
        AID_REGISTRY[params.aid],
        PLANS[params.plan],
        hero=params.hero, hero_gender=params.hero_gender,
        friend=params.friend, friend_gender=params.friend_gender,
        adult=params.adult, trait=params.trait, delay=params.delay,
        hero_age=params.hero_age, friend_age=params.friend_age, relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show hazard/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("hazards:", ", ".join(f"{a},{b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
