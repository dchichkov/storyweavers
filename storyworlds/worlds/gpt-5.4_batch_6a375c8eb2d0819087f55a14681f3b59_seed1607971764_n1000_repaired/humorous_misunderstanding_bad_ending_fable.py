#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py
========================================================================

A standalone story world for a tiny fable domain: **an eager animal hears a wise
warning, misunderstands one important word, shows off the wrong lesson, and ends
up with a funny but bad ending that proves why listening carefully matters.**

This world is built to make complete little tales rather than noun-swaps:
a need is introduced, a warning is given, a misunderstanding drives the turn,
and the ending image shows the cost of pride. The tone is light and child-facing,
with a humorous surface and a fable-like moral.

Run it
------
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py --hero fox --task quiet_crossing
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py --task muddy_path --warning tiptoe
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py --all
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/humorous_misunderstanding_bad_ending_fable.py --verify
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
        male = {"fox", "crow", "wolf", "frog", "goat"}
        female = {"hen", "duck", "mouse", "goose"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class HeroKind:
    id: str
    label: str
    boast_style: str
    feet: str
    voice: str
    traits: set[str] = field(default_factory=set)
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
class AdvisorKind:
    id: str
    label: str
    wise_style: str
    traits: set[str] = field(default_factory=set)
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
class Task:
    id: str
    place: str
    goal: str
    risk: str
    object_label: str
    wrong_noise: str
    outcome_image: str
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
class Warning:
    id: str
    action: str
    plain: str
    misunderstood_as: str
    wrong_action: str
    method_phrase: str
    sense: int
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
class Mood:
    id: str
    opener: str
    humorous_line: str
    closing_moral: str
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


def _r_noise_spills(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    task = world.facts["task_cfg"]
    if hero.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise_spills", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("goal").meters["lost"] += 1
    hero.memes["alarm"] += 1
    out.append("__lost__")
    return out


def _r_mud_slips(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    task = world.facts["task_cfg"]
    if task.id != "muddy_path":
        return out
    if hero.meters["slippery"] < THRESHOLD:
        return out
    sig = ("mud_slips", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["fallen"] += 1
    world.get("goal").meters["lost"] += 1
    hero.memes["alarm"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_spills", tag="physical", apply=_r_noise_spills),
    Rule(name="mud_slips", tag="physical", apply=_r_mud_slips),
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


def sensible_warnings() -> list[Warning]:
    return [w for w in WARNINGS.values() if w.sense >= SENSE_MIN]


def valid_combo(task: Task, warning: Warning) -> bool:
    if warning.sense < SENSE_MIN:
        return False
    if task.id == "quiet_crossing":
        return warning.id in {"tiptoe", "whisper"}
    if task.id == "muddy_path":
        return warning.id in {"small_steps", "watch_ground"}
    if task.id == "sleeping_lion":
        return warning.id in {"whisper", "tiptoe"}
    return False


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for task_id, task in TASKS.items():
        for warning_id, warning in WARNINGS.items():
            if valid_combo(task, warning):
                combos.append((task_id, warning_id))
    return combos


def predict_failure(task: Task, warning: Warning) -> dict:
    noisy = warning.wrong_action in {"stomp", "shout"}
    slippery = task.id == "muddy_path" and warning.wrong_action == "bounce"
    return {
        "noisy": noisy,
        "slippery": slippery,
        "fails": noisy or slippery,
    }


def explain_rejection(task: Task, warning: Warning) -> str:
    if warning.sense < SENSE_MIN:
        return (
            f"(No story: the warning '{warning.id}' is too weak or odd for this fable "
            f"(sense={warning.sense} < {SENSE_MIN}). Pick a plainer piece of advice.)"
        )
    return (
        f"(No story: '{warning.plain}' is not a sensible warning for {task.place}. "
        f"The misunderstanding must begin from advice that truly fits the task.)"
    )


def introduce(world: World, hero: Entity, advisor: Entity, task: Task, mood: Mood) -> None:
    hero.memes["pride"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{mood.opener} In the ferns beside {task.place}, a {hero.type} named "
        f"{hero.id} found {task.object_label} and longed to carry it home."
    )
    world.say(
        f"{hero.id} was quick of foot and quicker in talk, and {hero.pronoun()} liked "
        f"to sound as grand as a drum. Nearby sat {advisor.id} the {advisor.type}, "
        f"whose eyes missed very little."
    )


def explain_need(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"Yet there was a trouble. To reach the far side of {task.place}, "
        f"{hero.id} had to {task.goal}, and {task.risk}."
    )


def advise(world: World, advisor: Entity, hero: Entity, warning: Warning, task: Task) -> None:
    pred = predict_failure(task, warning)
    world.facts["predicted_fail"] = pred["fails"]
    world.facts["predicted_noisy"] = pred["noisy"]
    world.facts["predicted_slippery"] = pred["slippery"]
    hero.memes["trust"] += 1
    world.say(
        f'"{warning.plain}," said {advisor.id}. "{warning.method_phrase}"'
    )


def misunderstand(world: World, hero: Entity, warning: Warning, mood: Mood) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"But {hero.id} only heard the first useful sound and twisted the sense. "
        f"{hero.pronoun().capitalize()} decided that {warning.action} must surely mean "
        f'"{warning.misunderstood_as}."'
    )
    world.say(
        f'{hero.pronoun().capitalize()} gave a {mood.humorous_line} grin and said, '
        f'"At last! Advice worthy of me."'
    )


def perform_wrong_action(world: World, hero: Entity, task: Task, warning: Warning) -> None:
    if warning.wrong_action in {"stomp", "shout"}:
        hero.meters["noise"] += 1
    if task.id == "muddy_path" and warning.wrong_action == "bounce":
        hero.meters["slippery"] += 1
    hero.memes["showing_off"] += 1
    propagate(world, narrate=False)
    if warning.wrong_action == "stomp":
        world.say(
            f"So the {hero.type} marched forward with proud, pounding {hero.attrs['feet_word']}, "
            f"making {task.wrong_noise}."
        )
    elif warning.wrong_action == "shout":
        world.say(
            f"So {hero.id} puffed out {hero.pronoun('possessive')} chest and cried the advice "
            f"back to the trees in {hero.attrs['voice_word']} tones."
        )
    elif warning.wrong_action == "bounce":
        world.say(
            f"So {hero.id} tried to cross by bouncing from one muddy hump to the next, "
            f"as if springy knees could outsmart slime."
        )
    else:
        world.say(
            f"So {hero.id} did exactly the wrong thing in the wrong way."
        )


def bad_result(world: World, hero: Entity, task: Task) -> None:
    goal = world.get("goal")
    if task.id == "muddy_path":
        world.say(
            f"The mud answered with a rude little slurp. {hero.id} skidded, sat down hard, "
            f"and {task.outcome_image}."
        )
    else:
        world.say(
            f"At once, {task.outcome_image}. In a blink, the prize was gone and the lesson "
            f"stood where the supper had been."
        )
    if goal.meters["lost"] >= THRESHOLD:
        hero.memes["shame"] += 1
        hero.memes["hunger"] += 1


def closing(world: World, hero: Entity, advisor: Entity, mood: Mood, task: Task) -> None:
    world.say(
        f"{advisor.id} blinked once and said no more. {hero.id} went home with an empty belly "
        f"and a full memory."
    )
    world.say(
        f"{mood.closing_moral} Thus the woods learned a humorous little truth: "
        f"ears that are full of pride do not leave much room for sense."
    )


def tell(
    hero_cfg: HeroKind,
    advisor_cfg: AdvisorKind,
    task_cfg: Task,
    warning_cfg: Warning,
    mood_cfg: Mood,
    hero_name: str = "Rufus",
    advisor_name: str = "Aunt Owl",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_cfg.id,
        label=hero_cfg.label,
        role="hero",
        attrs={"feet_word": hero_cfg.feet, "voice_word": hero_cfg.voice},
    ))
    advisor = world.add(Entity(
        id=advisor_name,
        kind="character",
        type=advisor_cfg.id,
        label=advisor_cfg.label,
        role="advisor",
        attrs={},
    ))
    goal = world.add(Entity(
        id="goal",
        kind="thing",
        type="prize",
        label=task_cfg.object_label,
        role="goal",
        attrs={},
    ))

    world.facts.update(
        hero=hero,
        advisor=advisor,
        goal=goal,
        hero_cfg=hero_cfg,
        advisor_cfg=advisor_cfg,
        task_cfg=task_cfg,
        warning_cfg=warning_cfg,
        mood_cfg=mood_cfg,
    )

    introduce(world, hero, advisor, task_cfg, mood_cfg)
    explain_need(world, hero, task_cfg)

    world.para()
    advise(world, advisor, hero, warning_cfg, task_cfg)
    misunderstand(world, hero, warning_cfg, mood_cfg)
    perform_wrong_action(world, hero, task_cfg, warning_cfg)

    world.para()
    bad_result(world, hero, task_cfg)
    closing(world, hero, advisor, mood_cfg, task_cfg)

    world.facts.update(
        failed=world.get("goal").meters["lost"] >= THRESHOLD,
        noisy=hero.meters["noise"] >= THRESHOLD,
        slippery=hero.meters["slippery"] >= THRESHOLD,
        fallen=hero.meters["fallen"] >= THRESHOLD,
    )
    return world


HEROES = {
    "fox": HeroKind(
        id="fox",
        label="fox",
        boast_style="smooth",
        feet="paws",
        voice="silvery",
        traits={"proud", "quick"},
    ),
    "crow": HeroKind(
        id="crow",
        label="crow",
        boast_style="scratchy",
        feet="claws",
        voice="cawing",
        traits={"proud", "noisy"},
    ),
    "frog": HeroKind(
        id="frog",
        label="frog",
        boast_style="bouncy",
        feet="toes",
        voice="croaking",
        traits={"springy", "eager"},
    ),
}

ADVISORS = {
    "owl": AdvisorKind(
        id="owl",
        label="owl",
        wise_style="calm",
        traits={"wise"},
    ),
    "tortoise": AdvisorKind(
        id="tortoise",
        label="tortoise",
        wise_style="slow",
        traits={"careful"},
    ),
}

TASKS = {
    "quiet_crossing": Task(
        id="quiet_crossing",
        place="the hanging bridge",
        goal="cross without a sound",
        risk="one clatter would send the roast plum tumbling into the ravine",
        object_label="a roast plum",
        wrong_noise="the boards knock like wooden spoons",
        outcome_image="the bridge rattled, and the roast plum bounced away into the ferny dark",
        tags={"bridge", "quiet"},
    ),
    "muddy_path": Task(
        id="muddy_path",
        place="the clay lane",
        goal="carry a pear across the mud",
        risk="one foolish slip would send the pear rolling into the ditch",
        object_label="a yellow pear",
        wrong_noise="wet pats and silly splashes",
        outcome_image="the pear skipped from his grasp and sailed into the ditch while mud sat on his nose",
        tags={"mud", "careful"},
    ),
    "sleeping_lion": Task(
        id="sleeping_lion",
        place="the lion's cave-mouth",
        goal="steal past with a fig",
        risk="one loud sound would wake the lion and make the fig fly from fright",
        object_label="a purple fig",
        wrong_noise="a clack and a yelp together",
        outcome_image="the lion snorted awake, and the fig shot from the hero's grip like a pebble from a sling",
        tags={"lion", "quiet"},
    ),
}

WARNINGS = {
    "tiptoe": Warning(
        id="tiptoe",
        action="tiptoe",
        plain="Tiptoe, little friend",
        misunderstood_as="stamp with style",
        wrong_action="stomp",
        method_phrase="Let the ground barely know you are there.",
        sense=3,
        tags={"quiet", "careful"},
    ),
    "whisper": Warning(
        id="whisper",
        action="whisper",
        plain="Whisper, and even your feet will remember gentleness",
        misunderstood_as="shout clearly so everyone can hear good advice",
        wrong_action="shout",
        method_phrase="Soft things pass where loud things are stopped.",
        sense=3,
        tags={"quiet", "voice"},
    ),
    "small_steps": Warning(
        id="small_steps",
        action="take small steps",
        plain="Take small steps",
        misunderstood_as="take springy leaps",
        wrong_action="bounce",
        method_phrase="Mud loves a hurried foot.",
        sense=3,
        tags={"mud", "careful"},
    ),
    "watch_ground": Warning(
        id="watch_ground",
        action="watch the ground",
        plain="Watch the ground and place each foot wisely",
        misunderstood_as="watch only the clouds and trust your luck",
        wrong_action="bounce",
        method_phrase="The earth tells on itself when it is slippery.",
        sense=2,
        tags={"mud", "careful"},
    ),
    "sing": Warning(
        id="sing",
        action="sing",
        plain="Sing your courage",
        misunderstood_as="sing louder than thunder",
        wrong_action="shout",
        method_phrase="A true song can steady the heart.",
        sense=1,
        tags={"odd"},
    ),
}

MOODS = {
    "dry": Mood(
        id="dry",
        opener="Once, under a sky as pale as a shell,",
        humorous_line="very pleased and very foolish",
        closing_moral="Many creatures can run fast; only a few can listen slowly.",
        tags={"fable"},
    ),
    "merry": Mood(
        id="merry",
        opener="One bright morning,",
        humorous_line="cheerful and ridiculous",
        closing_moral="The proud often trip over the very warning set to save them.",
        tags={"fable", "humorous"},
    ),
}


@dataclass
class StoryParams:
    hero: str
    advisor: str
    task: str
    warning: str
    mood: str
    hero_name: str
    advisor_name: str
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


GIRLISH_NAMES = ["Mina", "Tansy", "Pip", "Dot"]
BOYISH_NAMES = ["Rufus", "Bram", "Ned", "Tobin"]
ADVISOR_NAMES = ["Aunt Owl", "Old Mossback", "Grey Shell", "Master Owl"]

KNOWLEDGE = {
    "quiet": [
        (
            "Why is it useful to move quietly sometimes?",
            "Moving quietly helps you avoid waking someone, startling an animal, or dropping what you are carrying. Soft steps can be safer than proud, noisy ones."
        )
    ],
    "mud": [
        (
            "Why can mud make you fall?",
            "Mud is slippery because your feet cannot grip it well. If you hurry or leap, you can slide and lose what you are holding."
        )
    ],
    "careful": [
        (
            "What does it mean to be careful?",
            "Being careful means you slow down, pay attention, and do things in a safe way. Careful creatures often finish the job that careless ones lose."
        )
    ],
    "voice": [
        (
            "What is a whisper?",
            "A whisper is a very soft way of speaking. People whisper when they do not want to wake someone or make a loud noise."
        )
    ],
    "lion": [
        (
            "Why should you not wake a sleeping lion?",
            "A sleeping lion is safest when left alone. Waking a big animal suddenly can scare you both and make trouble very fast."
        )
    ],
    "bridge": [
        (
            "Why can a shaky bridge be hard to cross?",
            "A shaky bridge moves under your feet, so noise and wobbling can make you lose balance. Slow steps help keep things steady."
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "quiet", "mud", "careful", "voice", "lion"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task_cfg"]
    warning = f["warning_cfg"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the word "humorous" in spirit and shows a misunderstanding leading to a bad ending.',
        f"Tell a child-facing animal fable where a {hero.type} misunderstands the advice '{warning.plain}' while trying to cross {task.place}, and loses {task.object_label}.",
        f"Write a humorous little fable with a foolish hero, a wise adviser, and a moral about listening carefully."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    advisor = f["advisor"]
    task = f["task_cfg"]
    warning = f["warning_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who wanted to carry {task.object_label} home, and {advisor.id} the {advisor.type}, who gave wise advice."
        ),
        (
            f"What problem did {hero.id} have?",
            f"{hero.id} had to {task.goal} at {task.place}. The trouble was that {task.risk}."
        ),
        (
            f"What advice did {advisor.id} give?",
            f"{advisor.id} told {hero.id}, '{warning.plain}' and explained, '{warning.method_phrase}' The advice was meant to help {hero.pronoun('object')} move safely."
        ),
        (
            f"How did the misunderstanding happen?",
            f"{hero.id} did not listen carefully and twisted {advisor.id}'s words into something showy and wrong. Because pride filled {hero.pronoun('possessive')} ears, {hero.pronoun()} heard '{warning.misunderstood_as}' instead of the careful meaning."
        ),
    ]
    if f["failed"]:
        if f["fallen"]:
            qa.append((
                f"Why did {hero.id} lose the prize?",
                f"{hero.id} tried to move in the wrong way on slippery mud, so {hero.pronoun()} fell and dropped it. The bad ending came from misunderstanding careful advice and then showing off."
            ))
        else:
            qa.append((
                f"Why did {hero.id} lose the prize?",
                f"{hero.id} made too much noise, and that ruined the crossing at once. The prize was lost because the warning was about gentleness, but {hero.pronoun()} turned it into bragging."
            ))
    qa.append((
        "What is the moral of the story?",
        "The story teaches that proud creatures may hear words without understanding them. If you want help, you must listen for the meaning and not only for the part that flatters you."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task_cfg"].tags) | set(world.facts["warning_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="fox",
        advisor="owl",
        task="quiet_crossing",
        warning="tiptoe",
        mood="merry",
        hero_name="Rufus",
        advisor_name="Aunt Owl",
    ),
    StoryParams(
        hero="crow",
        advisor="tortoise",
        task="sleeping_lion",
        warning="whisper",
        mood="dry",
        hero_name="Bram",
        advisor_name="Old Mossback",
    ),
    StoryParams(
        hero="frog",
        advisor="owl",
        task="muddy_path",
        warning="small_steps",
        mood="merry",
        hero_name="Tobin",
        advisor_name="Master Owl",
    ),
    StoryParams(
        hero="fox",
        advisor="tortoise",
        task="muddy_path",
        warning="watch_ground",
        mood="dry",
        hero_name="Ned",
        advisor_name="Grey Shell",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "bad_end"


ASP_RULES = r"""
warning_sensible(W) :- warning(W), sense(W,S), sense_min(M), S >= M.

valid(Task, Warn) :- task(Task), warning(Warn), warning_sensible(Warn), fits(Task, Warn).

noisy(Warn) :- wrong_action(Warn, stomp).
noisy(Warn) :- wrong_action(Warn, shout).
slippery(Task, Warn) :- task_kind(Task, muddy_path), wrong_action(Warn, bounce).

fails(Task, Warn) :- noisy(Warn).
fails(Task, Warn) :- slippery(Task, Warn).

outcome(Task, Warn, bad_end) :- valid(Task, Warn), fails(Task, Warn).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for advisor_id in ADVISORS:
        lines.append(asp.fact("advisor", advisor_id))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("task_kind", task_id, task.id))
    for warning_id, warning in WARNINGS.items():
        lines.append(asp.fact("warning", warning_id))
        lines.append(asp.fact("sense", warning_id, warning.sense))
        lines.append(asp.fact("wrong_action", warning_id, warning.wrong_action))
    fits = {
        "quiet_crossing": {"tiptoe", "whisper"},
        "muddy_path": {"small_steps", "watch_ground"},
        "sleeping_lion": {"whisper", "tiptoe"},
    }
    for task_id, warning_ids in fits.items():
        for warning_id in sorted(warning_ids):
            lines.append(asp.fact("fits", task_id, warning_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show warning_sensible/1."))
    return sorted(w for (w,) in asp.atoms(model, "warning_sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_warning", params.warning),
        "outcome_choice(O) :- chosen_task(T), chosen_warning(W), outcome(T,W,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome_choice/1."))
    atoms = asp.atoms(model, "outcome_choice")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sens = {w.id for w in sensible_warnings()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible warnings match ({sorted(py_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible warnings:")
        print("  python:", sorted(py_sens))
        print("  clingo:", sorted(asp_sens))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {s}")
            break

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
        smoke = generate(cases[0] if cases else CURATED[0])
        emit(smoke, trace=False, qa=False, header="SMOKE")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a humorous misunderstanding in a little fable with a bad ending."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--advisor", choices=ADVISORS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--advisor-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible task/warning pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.warning:
        task = TASKS[args.task]
        warning = WARNINGS[args.warning]
        if not valid_combo(task, warning):
            raise StoryError(explain_rejection(task, warning))
    if args.warning and WARNINGS[args.warning].sense < SENSE_MIN:
        task = TASKS[args.task] if args.task else TASKS["quiet_crossing"]
        raise StoryError(explain_rejection(task, WARNINGS[args.warning]))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.warning is None or combo[1] == args.warning)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    task_id, warning_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(HEROES))
    advisor_id = args.advisor or rng.choice(sorted(ADVISORS))
    mood_id = args.mood or rng.choice(sorted(MOODS))
    hero_name = args.hero_name or rng.choice(BOYISH_NAMES + GIRLISH_NAMES)
    advisor_name = args.advisor_name or rng.choice(ADVISOR_NAMES)
    return StoryParams(
        hero=hero_id,
        advisor=advisor_id,
        task=task_id,
        warning=warning_id,
        mood=mood_id,
        hero_name=hero_name,
        advisor_name=advisor_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        hero_cfg = HEROES[params.hero]
        advisor_cfg = ADVISORS[params.advisor]
        task_cfg = TASKS[params.task]
        warning_cfg = WARNINGS[params.warning]
        mood_cfg = MOODS[params.mood]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(task_cfg, warning_cfg):
        raise StoryError(explain_rejection(task_cfg, warning_cfg))

    world = tell(
        hero_cfg=hero_cfg,
        advisor_cfg=advisor_cfg,
        task_cfg=task_cfg,
        warning_cfg=warning_cfg,
        mood_cfg=mood_cfg,
        hero_name=params.hero_name,
        advisor_name=params.advisor_name,
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
        print(asp_program("", "#show valid/2.\n#show warning_sensible/1.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible warnings: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (task, warning) combos:\n")
        for task_id, warning_id in combos:
            print(f"  {task_id:14} {warning_id}")
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
            header = f"### {p.hero_name}: {p.task} with {p.warning} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
