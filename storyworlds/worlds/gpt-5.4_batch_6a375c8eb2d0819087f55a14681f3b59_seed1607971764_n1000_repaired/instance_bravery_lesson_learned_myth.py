#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py
==================================================================

A standalone story world in a gentle myth style: a child meets a valley that
echoes fear back at anyone who enters it alone. The child wants a golden fig
from an old tree to help the village feast, but the Echo Hollow magnifies fear
and can trap a lone traveler in circles. The brave choice is not "go alone no
matter what" but "ask for the right help and cross wisely."

This world models:
- typed entities with physical meters and emotional memes
- a reasonableness gate over valid (hero, helper, challenge) combinations
- a Python simulator and an inline ASP twin
- three Q&A sets grounded in world state, not English parsing

Run it
------
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py --hero child --helper crane
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py --helper pebble
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py --all
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/instance_bravery_lesson_learned_myth.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess", "maiden"}
        male = {"boy", "man", "father", "god", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Hero:
    id: str
    label: str
    type: str
    title: str
    virtue: str
    voice: str
    courage: int
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
class Helper:
    id: str
    label: str
    type: str
    phrase: str
    gift: str
    method: str
    power: int
    sense: int
    lesson: str
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
class Challenge:
    id: str
    place: str
    trouble: str
    need: int
    danger_line: str
    image: str
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


def _r_hollow_frightens(world: World) -> list[str]:
    hero = world.get("hero")
    hollow = world.get("hollow")
    helper = world.get("helper")
    if hero.meters["entered_hollow"] < THRESHOLD:
        return []
    sig = ("frighten",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fear_gain = max(0.0, hollow.meters["echo_force"] - helper.meters["steadying"])
    hero.memes["fear"] += fear_gain
    if fear_gain >= THRESHOLD:
        hollow.meters["circling"] += 1
    return []


def _r_help_clears_circling(world: World) -> list[str]:
    hero = world.get("hero")
    hollow = world.get("hollow")
    helper = world.get("helper")
    if hollow.meters["circling"] < THRESHOLD:
        return []
    if helper.meters["guiding"] < THRESHOLD:
        return []
    sig = ("clear_circling",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hollow.meters["circling"] = 0.0
    hero.memes["hope"] += 1
    return []


def _r_reach_tree(world: World) -> list[str]:
    hero = world.get("hero")
    hollow = world.get("hollow")
    tree = world.get("tree")
    helper = world.get("helper")
    if hero.meters["entered_hollow"] < THRESHOLD:
        return []
    if hollow.meters["circling"] >= THRESHOLD:
        return []
    if helper.meters["guiding"] < THRESHOLD:
        return []
    sig = ("reach_tree",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["reached"] += 1
    hero.memes["bravery"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hollow_frightens", tag="emotional", apply=_r_hollow_frightens),
    Rule(name="help_clears_circling", tag="social", apply=_r_help_clears_circling),
    Rule(name="reach_tree", tag="physical", apply=_r_reach_tree),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current_count = len(world.fired)
        for rule in CAUSAL_RULES:
            if len(world.fired) != current_count:
                changed = True
                break
    if narrate:
        for s in produced:
            world.say(s)
    return produced


HEROES = {
    "child": Hero(
        id="child",
        label="a village child named Ione",
        type="girl",
        title="Ione",
        virtue="quick heart",
        voice="clear",
        courage=2,
        tags={"child", "bravery"},
    ),
    "shepherd": Hero(
        id="shepherd",
        label="a young shepherd named Theron",
        type="boy",
        title="Theron",
        virtue="steady feet",
        voice="low",
        courage=3,
        tags={"shepherd", "bravery"},
    ),
    "potter": Hero(
        id="potter",
        label="a potter's daughter named Melia",
        type="girl",
        title="Melia",
        virtue="patient hands",
        voice="gentle",
        courage=2,
        tags={"potter", "bravery"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="owl",
        type="thing",
        phrase="a moon-eyed owl on an olive branch",
        gift="silver feathers that pointed the right way",
        method="flew ahead from stone to stone",
        power=3,
        sense=3,
        lesson="A brave heart listens when wisdom calls from the dark.",
        tags={"owl", "wisdom", "night"},
    ),
    "crane": Helper(
        id="crane",
        label="crane",
        type="thing",
        phrase="a white crane standing in the reeds",
        gift="a long bright plume",
        method="stepped through the mist and showed where the ground stayed firm",
        power=2,
        sense=3,
        lesson="Bravery is strongest when it walks carefully.",
        tags={"crane", "wisdom", "marsh"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="grandmother",
        type="woman",
        phrase="the hero's old grandmother, who remembered ancient paths",
        gift="a red thread tied around the wrist",
        method="taught an old road-song and waited at the edge until the song came back true",
        power=3,
        sense=3,
        lesson="For instance, the old knew what the young could not yet see.",
        tags={"grandmother", "elder", "song"},
    ),
    "pebble": Helper(
        id="pebble",
        label="pebble",
        type="thing",
        phrase="a smooth pebble picked up beside the road",
        gift="nothing more than its small round weight",
        method="did nothing but sit in a pocket",
        power=0,
        sense=1,
        lesson="A pebble cannot guide a traveler through living danger.",
        tags={"pebble"},
    ),
}

CHALLENGES = {
    "echo_hollow": Challenge(
        id="echo_hollow",
        place="Echo Hollow",
        trouble="a valley where frightened footsteps folded back on themselves",
        need=2,
        danger_line="The hollow loved to throw a fearful voice back twice as loud.",
        image="mist curling between black cypress roots",
        reward="a golden fig from the Dawn Tree",
        tags={"valley", "echo", "fig"},
    ),
    "reed_maze": Challenge(
        id="reed_maze",
        place="the Reed Maze",
        trouble="a marsh path that vanished when panic made the eyes hurry",
        need=2,
        danger_line="In the reeds, the wrong step sank and the right step hid itself.",
        image="water shining between green walls",
        reward="a blue water-lily seed pod for the shrine bowl",
        tags={"marsh", "reeds", "lily"},
    ),
    "shadow_ford": Challenge(
        id="shadow_ford",
        place="the Shadow Ford",
        trouble="a shallow crossing where ripples copied every trembling thought",
        need=3,
        danger_line="At the ford, fear made the water look deeper than it was.",
        image="dark water holding a thin line of stars",
        reward="a white river stone for the altar step",
        tags={"river", "crossing", "stone"},
    ),
}


def valid_combo(hero: Hero, helper: Helper, challenge: Challenge) -> bool:
    return helper.sense >= SENSE_MIN and helper.power >= challenge.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero_id, hero in HEROES.items():
        for helper_id, helper in HELPERS.items():
            for challenge_id, challenge in CHALLENGES.items():
                if valid_combo(hero, helper, challenge):
                    combos.append((hero_id, helper_id, challenge_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    helper: str
    challenge: str
    village_name: str = "Aster Glen"
    elder_name: str = "Neris"
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


def predict_outcome(hero: Hero, helper: Helper, challenge: Challenge) -> dict:
    safe = helper.sense >= SENSE_MIN and helper.power >= challenge.need
    return {
        "safe": safe,
        "circles": not safe,
        "reaches_reward": safe,
    }


def introduce(world: World, hero_ent: Entity, challenge: Challenge) -> None:
    world.say(
        f"In the old days, when dawn was said to walk the hills in sandals of light, "
        f"there stood a small village called {world.facts['village_name']}. In that place lived "
        f"{hero_ent.id}, known for {world.facts['hero_cfg'].virtue} and a {world.facts['hero_cfg'].voice} voice."
    )
    world.say(
        f"Above the village lay {challenge.place}, {challenge.trouble}. Beyond it grew the Dawn Tree, "
        f"and on one bright branch hung {challenge.reward}."
    )


def need(world: World, hero_ent: Entity, elder_ent: Entity, challenge: Challenge) -> None:
    hero_ent.memes["care"] += 1
    world.say(
        f"That year the village feast had come lean, and {elder_ent.id}, keeper of the shrine lamp, "
        f"said that one gift from the Dawn Tree would be enough to begin the songs."
    )
    world.say(
        f'{hero_ent.id} lifted {hero_ent.pronoun("possessive")} chin. "I will cross {challenge.place} and bring it back," '
        f'{hero_ent.pronoun()} said.'
    )


def warning(world: World, elder_ent: Entity, challenge: Challenge) -> None:
    world.say(
        f'''But {elder_ent.id} answered softly, "{challenge.danger_line} "'''
        f"No one should go there with pride alone."
    )


def find_helper(world: World, hero_ent: Entity, helper: Helper) -> None:
    hero_ent.memes["hope"] += 1
    world.say(
        f"At the edge of the path, {hero_ent.id} found {helper.phrase}. "
        f"It offered {helper.gift} and {helper.method}."
    )


def choose_help(world: World, hero_ent: Entity, helper: Helper) -> None:
    if helper.sense >= SENSE_MIN:
        hero_ent.memes["wisdom"] += 1
        world.say(
            f"Then {hero_ent.id} understood a thing brave people sometimes forget: "
            f"courage does not shrink when it accepts help."
        )
    else:
        hero_ent.memes["pride"] += 1
        world.say(
            f"{hero_ent.id} mistook a small comfort for true guidance and stepped on, "
            f"thinking that would be enough."
        )


def enter_hollow(world: World, hero_ent: Entity, helper_ent: Entity, challenge: Challenge, helper: Helper) -> None:
    hero_ent.meters["steps_taken"] = 1.0
    hero_ent.meters["entered"] = 1.0
    hero_ent.meters["entered_hollow"] = 1.0
    helper_ent.meters["steadying"] = float(helper.power)
    if helper.sense >= SENSE_MIN:
        helper_ent.meters["guiding"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"So {hero_ent.id} entered {challenge.place}. There was {challenge.image}, "
        f"and every sound seemed to listen before it spoke."
    )
    if world.get("hollow").meters["circling"] >= THRESHOLD:
        world.say(
            f"Soon the path bent strangely, and {hero_ent.id}'s own breathing came back like footsteps behind "
            f"{hero_ent.pronoun('object')}."
        )
    else:
        world.say(
            f"The fear rose for a moment, yet the offered sign held true, and the path did not twist."
        )


def turn(world: World, hero_ent: Entity, helper: Helper, challenge: Challenge) -> None:
    hollow = world.get("hollow")
    tree = world.get("tree")
    if hollow.meters["circling"] >= THRESHOLD or tree.meters["reached"] < THRESHOLD:
        hero_ent.memes["fear"] += 1
        world.say(
            f"{hero_ent.id} stopped among the shadows and knew this was the hard part of bravery: "
            f"not pretending fear was gone, but refusing to let fear be the guide."
        )
        world.say(
            f"{hero_ent.pronoun().capitalize()} turned back before the hollow could keep {hero_ent.pronoun('object')}, "
            f"and returned with the lesson already growing in {hero_ent.pronoun('possessive')} heart."
        )
        world.facts["outcome"] = "turned_back"
        return
    tree.meters["gift_taken"] += 1
    hero_ent.meters["reward_carried"] += 1
    hero_ent.memes["joy"] += 1
    world.say(
        f"Step by step, {hero_ent.id} reached the Dawn Tree and took {challenge.reward}. "
        f"The branch bowed as if the morning itself had given consent."
    )
    world.facts["outcome"] = "success"


def return_home(world: World, hero_ent: Entity, elder_ent: Entity, helper: Helper, challenge: Challenge) -> None:
    if world.facts["outcome"] == "success":
        hero_ent.memes["lesson_learned"] += 1
        world.say(
            f"When {hero_ent.id} came home, the lamp of {elder_ent.id} shone beside the feast stones, "
            f"and the village children ran to see the gift."
        )
        world.say(
            f'{hero_ent.id} said, "I crossed because I was brave, but I returned because I listened." '
            f"That was the lesson the village remembered."
        )
        world.say(
            f"From then on, whenever young feet hurried toward danger, the elders would say, "
            f'"{helper.lesson}"'
        )
    else:
        hero_ent.memes["lesson_learned"] += 1
        world.say(
            f"When {hero_ent.id} came home empty-handed, {elder_ent.id} did not scold {hero_ent.pronoun('object')}. "
            f"Instead, the old keeper made room by the lamp and listened."
        )
        world.say(
            f'{hero_ent.id} said, "For instance, I thought going on alone would make me braver. '
            f'But the hollow showed me that wisdom must walk beside courage."'
        )
        world.say(
            f"The next dawn, no one praised foolish daring. They praised the child who had learned the right lesson "
            f"before harm grew large."
        )


def tell(hero: Hero, helper: Helper, challenge: Challenge, village_name: str, elder_name: str) -> World:
    world = World()
    hero_ent = world.add(Entity(id=hero.title, kind="character", type=hero.type, label=hero.label, role="hero"))
    elder_ent = world.add(Entity(id=elder_name, kind="character", type="woman", label="the elder", role="elder"))
    helper_ent = world.add(Entity(id="helper", kind="thing", type=helper.type, label=helper.label, role="helper"))
    hollow = world.add(Entity(id="hollow", kind="thing", type="place", label=challenge.place, role="challenge"))
    tree = world.add(Entity(id="tree", kind="thing", type="tree", label="Dawn Tree", role="goal"))

    hollow.meters["echo_force"] = float(challenge.need)
    helper_ent.meters["steadying"] = 0.0
    helper_ent.meters["guiding"] = 0.0
    hero_ent.meters["entered_hollow"] = 0.0
    hero_ent.meters["entered"] = 0.0
    hero_ent.meters["reward_carried"] = 0.0
    hero_ent.meters["steps_taken"] = 0.0
    tree.meters["reached"] = 0.0
    tree.meters["gift_taken"] = 0.0
    hollow.meters["circling"] = 0.0
    hero_ent.memes["fear"] = 0.0
    hero_ent.memes["hope"] = 0.0
    hero_ent.memes["bravery"] = float(hero.courage)
    hero_ent.memes["lesson_learned"] = 0.0
    hero_ent.memes["wisdom"] = 0.0
    hero_ent.memes["pride"] = 0.0
    hero_ent.memes["joy"] = 0.0
    hero_ent.memes["care"] = 0.0

    world.facts.update(
        hero=hero_ent,
        elder=elder_ent,
        helper=helper_ent,
        hollow=hollow,
        tree=tree,
        hero_cfg=hero,
        helper_cfg=helper,
        challenge_cfg=challenge,
        village_name=village_name,
        elder_name=elder_name,
        prediction=predict_outcome(hero, helper, challenge),
        outcome="",
    )

    introduce(world, hero_ent, challenge)
    need(world, hero_ent, elder_ent, challenge)

    world.para()
    warning(world, elder_ent, challenge)
    find_helper(world, hero_ent, helper)
    choose_help(world, hero_ent, helper)

    world.para()
    enter_hollow(world, hero_ent, helper_ent, challenge, helper)
    turn(world, hero_ent, helper, challenge)

    world.para()
    return_home(world, hero_ent, elder_ent, helper, challenge)
    return world


KNOWLEDGE = {
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story told in a grand, memorable way. It often explains a lesson, a custom, or why people remember a place."
        )
    ],
    "owl": [
        (
            "Why is an owl a sign of wisdom in many stories?",
            "Owls seem watchful and calm, especially at night. That is why stories often use them as signs of seeing what others miss."
        )
    ],
    "crane": [
        (
            "Why can a crane fit a careful story?",
            "A crane moves slowly and tests the ground with each step. That makes it a good symbol for patient bravery."
        )
    ],
    "elder": [
        (
            "Why do myths often include an elder?",
            "An elder can remember old dangers and old paths. In stories, that memory helps younger people make wiser choices."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after hitting a surface. In a story, an echo can also stand for fear returning louder inside your mind."
        )
    ],
    "bravery": [
        (
            "Does bravery mean never being afraid?",
            "No. Bravery means doing the right thing even when fear is present. Very often it also means asking for help instead of acting foolishly."
        )
    ],
    "lesson": [
        (
            "What is a lesson learned in a story?",
            "It is the understanding a character gains after something hard happens. The ending shows that the character will act differently next time."
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "echo", "bravery", "lesson", "owl", "crane", "elder"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    challenge = f["challenge_cfg"]
    return [
        f'Write a short myth for a young child about bravery that includes the word "instance".',
        f"Tell a mythic story where {hero.id} crosses {challenge.place} and learns that courage works best with wise help from a {helper.label}.",
        f"Write a gentle legend with a clear lesson learned: a hero faces fear, chooses guidance, and returns changed."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper_cfg = f["helper_cfg"]
    challenge = f["challenge_cfg"]
    elder = f["elder"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who tried to cross {challenge.place} for the village. {elder.id} and the {helper_cfg.label} mattered because they helped shape the choice."
        ),
        (
            f"Why did {hero.id} want to go to {challenge.place}?",
            f"{hero.id} wanted to bring back {challenge.reward} so the village feast and shrine songs could begin. That need made the journey feel important, not just exciting."
        ),
        (
            f"What danger was hidden in {challenge.place}?",
            f"The danger was that fear could turn the path into circles and make a traveler lose the way. The place echoed frightened thoughts until they felt bigger than they really were."
        ),
    ]
    if helper_cfg.sense >= SENSE_MIN:
        qa.append(
            (
                f"How did the {helper_cfg.label} help {hero.id}?",
                f"The {helper_cfg.label} gave real guidance instead of empty comfort. Because it showed a true way through the danger, {hero.id} could keep going without letting fear lead."
            )
        )
    else:
        qa.append(
            (
                f"Why was the {helper_cfg.label} not enough to help {hero.id}?",
                f"It gave no real guidance, so it could not answer the danger of the place. {hero.id} learned that a small comfort is not the same thing as wise help."
            )
        )
    if outcome == "success":
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.id} learned that bravery and listening belong together. The hero succeeded not by pretending to fear nothing, but by accepting guidance and walking wisely."
            )
        )
        qa.append(
            (
                "How does the ending prove the hero changed?",
                f"{hero.id} returned with the gift and also with new understanding. At the end, the hero says that listening was part of the victory, which shows a deeper kind of courage."
            )
        )
    else:
        qa.append(
            (
                "Did turning back mean the hero was not brave?",
                f"No. Turning back before the danger grew worse was itself a wise brave choice. The hero returned safely and came home with a lesson instead of an injury."
            )
        )
        qa.append(
            (
                "What lesson did the village remember?",
                f"They remembered that foolish daring is not the same as bravery. The story taught them to keep courage and wisdom together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"myth", "echo", "bravery", "lesson"}
    helper_cfg = f["helper_cfg"]
    if "owl" in helper_cfg.tags:
        tags.add("owl")
    if "crane" in helper_cfg.tags:
        tags.add("crane")
    if "grandmother" in helper_cfg.tags or "elder" in helper_cfg.tags:
        tags.add("elder")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="child",
        helper="owl",
        challenge="echo_hollow",
        village_name="Aster Glen",
        elder_name="Neris",
    ),
    StoryParams(
        hero="shepherd",
        helper="crane",
        challenge="reed_maze",
        village_name="Hill-of-Reeds",
        elder_name="Thaleia",
    ),
    StoryParams(
        hero="potter",
        helper="grandmother",
        challenge="shadow_ford",
        village_name="Clay Lantern",
        elder_name="Doria",
    ),
]


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    return (
        f"(No story: the chosen helper '{helper_id}' is not wise enough for this myth "
        f"(sense={helper.sense} < {SENSE_MIN}). A mythic lesson here needs real guidance, "
        f"not a token object.)"
    )


def explain_combo(hero: Hero, helper: Helper, challenge: Challenge) -> str:
    if helper.sense < SENSE_MIN:
        return explain_helper(helper.id)
    if helper.power < challenge.need:
        return (
            f"(No story: {helper.label} cannot reasonably guide someone through {challenge.place}. "
            f"The challenge needs help power {challenge.need}, but this helper has only {helper.power}.)"
        )
    return "(No story: this combination is unreasonable for the myth.)"


ASP_RULES = r"""
valid(H, He, C) :- hero(H), helper(He), challenge(C), sensible(He), can_meet(He, C).
sensible(He) :- helper(He), sense(He, S), sense_min(M), S >= M.
can_meet(He, C) :- helper(He), challenge(C), power(He, P), need(C, N), P >= N.

success :- chosen_helper(He), chosen_challenge(C), sensible(He), can_meet(He, C).
outcome(success) :- success.
outcome(turned_back) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        lines.append(asp.fact("sense", helper_id, helper.sense))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("need", challenge_id, challenge.need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_challenge", params.challenge),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.helper not in HELPERS or params.challenge not in CHALLENGES:
        return "?"
    helper = HELPERS[params.helper]
    challenge = CHALLENGES[params.challenge]
    return "success" if valid_combo(HEROES[params.hero], helper, challenge) else "turned_back"


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
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child-facing myth about bravery, guidance, and a lesson learned."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--village-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


VILLAGE_NAMES = ["Aster Glen", "Laurel Fold", "Hill-of-Reeds", "Sun-Bowl", "Clay Lantern"]
ELDER_NAMES = ["Neris", "Thaleia", "Doria", "Myrine", "Eunoe"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.helper in HELPERS and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))

    if args.hero and args.hero not in HEROES:
        raise StoryError(f"(No story: unknown hero '{args.hero}'.)")
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{args.helper}'.)")
    if args.challenge and args.challenge not in CHALLENGES:
        raise StoryError(f"(No story: unknown challenge '{args.challenge}'.)")

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.helper is None or combo[1] == args.helper)
        and (args.challenge is None or combo[2] == args.challenge)
    ]
    if not combos:
        if args.hero and args.helper and args.challenge:
            raise StoryError(explain_combo(HEROES[args.hero], HELPERS[args.helper], CHALLENGES[args.challenge]))
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, helper_id, challenge_id = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero_id,
        helper=helper_id,
        challenge=challenge_id,
        village_name=args.village_name or rng.choice(VILLAGE_NAMES),
        elder_name=args.elder_name or rng.choice(ELDER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(No story: unknown hero '{params.hero}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(No story: unknown challenge '{params.challenge}'.)")

    hero = HEROES[params.hero]
    helper = HELPERS[params.helper]
    challenge = CHALLENGES[params.challenge]
    if not valid_combo(hero, helper, challenge):
        raise StoryError(explain_combo(hero, helper, challenge))

    world = tell(hero, helper, challenge, params.village_name, params.elder_name)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, helper, challenge) combos:\n")
        for hero_id, helper_id, challenge_id in combos:
            print(f"  {hero_id:10} {helper_id:12} {challenge_id}")
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
            header = f"### {p.hero}: {p.helper} at {p.challenge}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
