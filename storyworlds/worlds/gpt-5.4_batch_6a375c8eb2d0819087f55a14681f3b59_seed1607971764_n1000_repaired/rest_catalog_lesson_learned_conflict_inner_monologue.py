#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py
==================================================================================

A standalone story world for a tall-tale-flavored story about a child who tries
to do a giant cataloging job without stopping to rest, tangles the work, and
learns that a short rest can be part of doing a big job well.

The world models one tiny domain:

* a child helper in an exaggerated frontier place
* an enormous cataloging task
* a particular kind of strain from that task
* a fitting sort of rest that truly helps
* a conflict beat where the child pushes on anyway
* a mistake caused by strain
* a repair after a sensible rest

The story always includes the words "rest" and "catalog", uses inner monologue,
and ends with a clear lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --job peach_crate
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --rest_kind water_break
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --trace
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --json
    python storyworlds/worlds/gpt-5.4/rest_catalog_lesson_learned_conflict_inner_monologue.py --verify
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
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
class Setting:
    id: str
    place: str
    skyline: str
    boast: str
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
class Job:
    id: str
    label: str
    phrase: str
    object_plural: str
    giant_image: str
    strain: str
    mistake: str
    fix: str
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
class RestKind:
    id: str
    label: str
    phrase: str
    soothes: set[str]
    sense: int
    action: str
    return_glow: str
    qa_text: str
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
class Mood:
    id: str
    boast: str
    thought: str
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


def _r_strain_slows(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["strain"] < THRESHOLD:
        return out
    if ("slow", hero.id) in world.fired:
        return out
    world.fired.add(("slow", hero.id))
    hero.meters["accuracy"] -= 1
    hero.memes["frustration"] += 1
    out.append("__strain__")
    return out


def _r_pushing_causes_mixup(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    task = world.get("task")
    if hero.meters["strain"] < THRESHOLD or hero.memes["defiance"] < THRESHOLD:
        return out
    if ("mixup", hero.id) in world.fired:
        return out
    world.fired.add(("mixup", hero.id))
    task.meters["mixed_up"] += 1
    hero.memes["alarm"] += 1
    out.append("__mixup__")
    return out


def _r_rest_restores(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["rested"] < THRESHOLD:
        return out
    if ("restore", hero.id) in world.fired:
        return out
    world.fired.add(("restore", hero.id))
    hero.meters["strain"] = 0.0
    hero.meters["accuracy"] = max(hero.meters["accuracy"], 1.0)
    hero.memes["frustration"] = 0.0
    hero.memes["relief"] += 1
    out.append("__restored__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="strain_slows", tag="physical", apply=_r_strain_slows),
    Rule(name="pushing_causes_mixup", tag="physical", apply=_r_pushing_causes_mixup),
    Rule(name="rest_restores", tag="physical", apply=_r_rest_restores),
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


def compatible_rest(job: Job, rest_kind: RestKind) -> bool:
    return job.strain in rest_kind.soothes


def sensible_rests() -> list[RestKind]:
    return [r for r in REST_KINDS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for job_id, job in JOBS.items():
            for rest_id, rest_kind in REST_KINDS.items():
                for mood_id in MOODS:
                    if compatible_rest(job, rest_kind) and rest_kind.sense >= SENSE_MIN:
                        combos.append((setting_id, job_id, rest_id, mood_id))
    return combos


def explain_rejection(job: Job, rest_kind: RestKind) -> str:
    if rest_kind.sense < SENSE_MIN:
        return (
            f"(No story: {rest_kind.label} is known here, but it is not a sensible fix "
            f"for an overworked child. This world prefers kinder, more useful kinds of rest.)"
        )
    return (
        f"(No story: {rest_kind.label} does not help with {job.strain}. "
        f"A rest in this world must match the strain the job creates.)"
    )


def predict_mixup(world: World, job: Job) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    task = sim.get("task")
    hero.meters["strain"] += 1
    hero.memes["defiance"] += 1
    propagate(sim, narrate=False)
    return {
        "mixed_up": task.meters["mixed_up"] >= THRESHOLD,
        "accuracy": hero.meters["accuracy"],
    }


def introduce(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"In {setting.place}, where {setting.skyline}, {hero.id} helped {helper.label_word} "
        f"run a catalog desk so big it looked like a county fair had learned to count."
    )
    world.say(setting.boast)


def start_job(world: World, hero: Entity, job: Job) -> None:
    world.say(
        f"That morning, {hero.id} was set to {job.phrase}. "
        f"{job.giant_image}"
    )
    world.say(
        f"{hero.id} squared {hero.pronoun('possessive')} shoulders and thought, "
        f'"{hero.attrs["inner_boast"]}"'
    )


def warning(world: World, helper: Entity, hero: Entity, job: Job, rest_kind: RestKind) -> None:
    pred = predict_mixup(world, job)
    world.facts["predicted_mixup"] = pred["mixed_up"]
    world.facts["predicted_accuracy"] = pred["accuracy"]
    world.say(
        f'After a while, {helper.label_word.capitalize()} watched {hero.id} blink hard and said, '
        f'"Even a tall worker needs a little rest. Take {rest_kind.phrase} before this catalog starts '
        f'running ahead of your hands."'
    )


def defy(world: World, hero: Entity, mood: Mood) -> None:
    hero.meters["strain"] += 1
    hero.memes["defiance"] += 1
    hero.memes["stubborn"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {hero.id} puffed up like a weather rooster in a storm. "{mood.boast}" '
        f"{hero.pronoun().capitalize()} reached for another armful instead."
    )
    world.say(
        f"Inside, {hero.pronoun()} told {hero.pronoun('object')}self, "
        f'"{mood.thought}"'
    )


def mixup(world: World, hero: Entity, job: Job) -> None:
    task = world.get("task")
    if task.meters["mixed_up"] < THRESHOLD:
        return
    world.say(
        f"That was when the trouble came. {job.mistake}"
    )
    world.say(
        f"{hero.id} stopped short. {hero.pronoun('possessive').capitalize()} cheeks went hot, "
        f"and the mighty catalog looked less like a neat plan and more like a paper tornado."
    )


def conflict(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f'"I told you to rest," {helper.label_word} said, not mean, but firm as a fence post. '
        f'"Big jobs do not get smaller just because you hurry at them."'
    )
    world.say(
        f'For one breath, {hero.id} wanted to argue. Then {hero.pronoun()} looked at the mixed-up stack '
        f"and could not."
    )


def choose_rest(world: World, helper: Entity, hero: Entity, rest_kind: RestKind) -> None:
    hero.meters["rested"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} finally took {rest_kind.phrase}. {helper.label_word.capitalize()} stayed close, and "
        f"{hero.pronoun()} {rest_kind.action}."
    )
    world.say(
        f"As the rest settled in, {hero.id} thought, "
        f'"Maybe stopping for a minute does not mean quitting. Maybe it means coming back strong."'
    )


def repair(world: World, hero: Entity, helper: Entity, job: Job, rest_kind: RestKind) -> None:
    task = world.get("task")
    task.meters["mixed_up"] = 0.0
    task.meters["sorted"] += 1
    hero.memes["learning"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"Then {hero.id} went back to work. {rest_kind.return_glow} and {job.fix}"
    )
    world.say(
        f'Soon the whole catalog lay in order, straight as corn rows and twice as proud. '
        f'"You were right," {hero.id} admitted. "A little rest saved the whole day."'
    )


def ending(world: World, hero: Entity, helper: Entity, job: Job) -> None:
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"By sundown, even the shadows seemed organized. {hero.id} had learned that in a place where "
        f"jobs were taller than barns, a wise pause could be part of the work."
    )
    world.say(
        f"After that, whenever {hero.pronoun()} faced {job.object_plural} enough to make the rafters bow, "
        f"{hero.id} still worked hard—but {hero.pronoun()} took rest before pride could tie the catalog in knots again."
    )


def tell(
    setting: Setting,
    job: Job,
    rest_kind: RestKind,
    mood: Mood,
    hero_name: str = "Molly",
    hero_type: str = "girl",
    helper_type: str = "uncle",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            role="hero",
            traits=["eager", "strong"],
            attrs={"inner_boast": ""},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label=helper_type,
            role="helper",
            traits=["steady"],
            attrs={},
        )
    )
    task = world.add(
        Entity(
            id="task",
            kind="thing",
            type="catalog_task",
            label=job.label,
            role="task",
            attrs={},
        )
    )

    hero.attrs["inner_boast"] = mood.thought.split(".")[0] if "." in mood.thought else mood.thought
    hero.meters["accuracy"] = 1.0
    hero.meters["strain"] = 0.0
    hero.meters["rested"] = 0.0
    task.meters["mixed_up"] = 0.0
    task.meters["sorted"] = 0.0
    world.facts.update(
        setting=setting,
        job=job,
        rest_kind=rest_kind,
        mood=mood,
        hero=hero,
        helper=helper,
        task=task,
        mixup=False,
        resolved=False,
        lesson=False,
    )

    introduce(world, hero, helper, setting)
    start_job(world, hero, job)

    world.para()
    warning(world, helper, hero, job, rest_kind)
    defy(world, hero, mood)
    mixup(world, hero, job)
    conflict(world, helper, hero)

    world.para()
    choose_rest(world, helper, hero, rest_kind)
    repair(world, hero, helper, job, rest_kind)
    ending(world, hero, helper, job)

    world.facts["mixup"] = task.meters["sorted"] >= THRESHOLD or task.meters["mixed_up"] >= THRESHOLD
    world.facts["resolved"] = task.meters["sorted"] >= THRESHOLD
    world.facts["lesson"] = hero.memes["learning"] >= THRESHOLD
    return world


SETTINGS = {
    "prairie_depot": Setting(
        id="prairie_depot",
        place="the Prairie Parcel Depot",
        skyline="the shelves climbed so high they tickled passing clouds",
        boast="Folks said the wind had to duck its head to get through the doorway.",
        tags={"depot", "prairie"},
    ),
    "river_wharf": Setting(
        id="river_wharf",
        place="the Riverboat Counting Wharf",
        skyline="the loading cranes leaned over the water like giant fishing poles",
        boast="The place was so busy that even the gulls sounded as if they were calling out order numbers.",
        tags={"wharf", "river"},
    ),
    "mesa_storehouse": Setting(
        id="mesa_storehouse",
        place="the Red Mesa Storehouse",
        skyline="the catalog shelves stood against the cliff like wooden ladders for the moon",
        boast="At noon the dust glowed gold, and every box seemed to brag about how far it had come.",
        tags={"mesa", "storehouse"},
    ),
}

JOBS = {
    "seed_packets": Job(
        id="seed_packets",
        label="seed packet catalog",
        phrase="sort the seed packet catalog by hand",
        object_plural="seed packets",
        giant_image="There were so many little envelopes that if you laid them end to end, they might have stitched one field to the next.",
        strain="dusty_eyes",
        mistake="A sneezing blink sent bean packets into the beet pile and pumpkin cards clear into the onion stack.",
        fix="with cooler eyes and steadier fingers, the seed packet rows marched back into place",
        tags={"seed", "catalog", "dust"},
    ),
    "boot_orders": Job(
        id="boot_orders",
        label="boot order catalog",
        phrase="stack the boot order catalog into proper piles",
        object_plural="boot orders",
        giant_image="The boot orders were so many and so thick that each stack looked like a short log cabin built of paper.",
        strain="sore_feet",
        mistake="Trying to hurry on tired feet, {hero} bumped the low stool, and boot orders for tiny feet slid under the pile for giant ranch hands.",
        fix="with a calmer stance and a steadier reach, the boot orders lined up by size again",
        tags={"boots", "catalog", "feet"},
    ),
    "peach_crate": Job(
        id="peach_crate",
        label="peach crate catalog",
        phrase="mark the peach crate catalog before the wagons rolled out",
        object_plural="peach crate labels",
        giant_image="There were enough peach labels to wallpaper a barn, a church, and half a polite argument.",
        strain="hot_head",
        mistake="Heat and hurry muddled the count, and the early crates got the late labels while the sweetest peaches waited with the wrong tags.",
        fix="with a cool head and patient eyes, the labels found the right crates again",
        tags={"peach", "catalog", "heat"},
    ),
}

REST_KINDS = {
    "shade_break": RestKind(
        id="shade_break",
        label="a shade break",
        phrase="a short rest under the shady awning",
        soothes={"hot_head", "dusty_eyes"},
        sense=3,
        action="closed tired eyes and let the heat slip away",
        return_glow="The world looked quieter and straighter afterward,",
        qa_text="rested in the shade until the heat and blinking passed",
        tags={"shade", "rest"},
    ),
    "water_break": RestKind(
        id="water_break",
        label="a water break",
        phrase="a short rest with cool water at the pump",
        soothes={"hot_head", "dusty_eyes"},
        sense=3,
        action="drank slowly and splashed a little cool water on a warm face",
        return_glow="The dusty blur cleared and the hurry drained away,",
        qa_text="took a water break and cooled down before trying again",
        tags={"water", "rest"},
    ),
    "bench_break": RestKind(
        id="bench_break",
        label="a bench break",
        phrase="a short rest on the broad pine bench",
        soothes={"sore_feet"},
        sense=3,
        action="sat long enough for aching legs and feet to stop fussing",
        return_glow="When the wobble left the knees,",
        qa_text="sat on the bench until tired feet stopped wobbling",
        tags={"bench", "rest"},
    ),
    "whistle_break": RestKind(
        id="whistle_break",
        label="a whistle break",
        phrase="a minute spent whistling louder at the ceiling",
        soothes=set(),
        sense=1,
        action="made a brave noise but did not actually feel better",
        return_glow="The ceiling had heard a fine tune, but",
        qa_text="whistled at the ceiling",
        tags={"silly"},
    ),
}

MOODS = {
    "stubborn": Mood(
        id="stubborn",
        boast="I can finish before a jackrabbit blinks.",
        thought="If I stop now, the whole mountain of work will laugh at me. I had better keep going.",
        tags={"stubborn"},
    ),
    "proud": Mood(
        id="proud",
        boast="I can outwork a whole row of grown-ups.",
        thought="A grand worker does not need rest for one little minute. I will prove it.",
        tags={"proud"},
    ),
    "hasty": Mood(
        id="hasty",
        boast="I can whip this job flat before the kettle sings.",
        thought="If I hurry hard enough, I will beat the trouble before it starts. Surely that is the same as resting.",
        tags={"hasty"},
    ),
}

GIRL_NAMES = ["Molly", "June", "Ada", "Nell", "Lucy", "Clara", "Ruth", "Hattie"]
BOY_NAMES = ["Eli", "Cal", "Tom", "Wes", "Ned", "Jesse", "Luke", "Beau"]


@dataclass
class StoryParams:
    setting: str
    job: str
    rest_kind: str
    mood: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
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


def _job_text(job: Job, hero_name: str) -> Job:
    if "{hero}" not in job.mistake:
        return job
    return Job(
        id=job.id,
        label=job.label,
        phrase=job.phrase,
        object_plural=job.object_plural,
        giant_image=job.giant_image,
        strain=job.strain,
        mistake=job.mistake.format(hero=hero_name),
        fix=job.fix,
        tags=set(job.tags),
    )


KNOWLEDGE = {
    "catalog": [
        (
            "What is a catalog?",
            "A catalog is an organized list of things, often with names or numbers, so people can find what they need. It helps a big pile of items make sense."
        )
    ],
    "rest": [
        (
            "Why can rest help you work better?",
            "Rest gives your body and mind a little time to recover. After a short break, it is easier to notice mistakes and do careful work."
        )
    ],
    "shade": [
        (
            "Why does shade help on a hot day?",
            "Shade blocks the hot sun, so your body does not have to work as hard to cool itself. That can help your head feel clearer."
        )
    ],
    "water": [
        (
            "Why can drinking water help when you feel hot or tired?",
            "Water helps your body stay cool and comfortable. When you are less hot and dry, it is easier to think and move carefully."
        )
    ],
    "bench": [
        (
            "Why is sitting down helpful when your feet are tired?",
            "Sitting lets your legs and feet stop carrying your weight for a moment. That short rest can make you steadier when you stand up again."
        )
    ],
    "dust": [
        (
            "Why can dusty work bother your eyes?",
            "Tiny bits of dust can make your eyes feel dry and itchy. When your eyes blink too much, careful sorting gets harder."
        )
    ],
    "heat": [
        (
            "Why is it harder to think clearly when you get too hot?",
            "When you are too hot, your body feels uncomfortable and distracted. That makes careful counting and sorting harder."
        )
    ],
    "feet": [
        (
            "How can tired feet cause mistakes?",
            "If your feet ache, you may wobble or rush to be done. Then your hands and eyes are more likely to miss where things belong."
        )
    ],
}
KNOWLEDGE_ORDER = ["catalog", "rest", "shade", "water", "bench", "dust", "heat", "feet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job"]
    rest_kind = f["rest_kind"]
    return [
        (
            f'Write a tall-tale-style story for a 3-to-5-year-old about a child helping with a giant catalog, '
            f'getting into trouble by refusing rest, and learning a lesson.'
        ),
        (
            f"Tell a frontier-flavored story where {hero.label} argues with {hero.pronoun('possessive')} "
            f"{helper.label_word} because {hero.pronoun()} wants to finish the {job.label} without stopping, "
            f"but a short rest saves the work."
        ),
        (
            f'Write a playful exaggeration that includes the words "rest" and "catalog", uses inner monologue, '
            f"and ends with the child admitting that resting helped."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job"]
    rest_kind = f["rest_kind"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child helping at {setting.place}, and {hero.pronoun('possessive')} "
            f"{helper.label_word} who watches the work. They are trying to keep a giant catalog in order."
        ),
        (
            f"What job was {hero.label} trying to do?",
            f"{hero.label} was trying to {job.phrase}. In this tall tale, the job was so huge it sounded bigger than an ordinary day's work."
        ),
        (
            f"Why did {helper.label_word} tell {hero.label} to rest?",
            f"{helper.label_word.capitalize()} could see that the work was making {hero.label} worn out. "
            f"If {hero.pronoun()} kept pushing, the catalog would get mixed up instead of finished."
        ),
        (
            f"What was the conflict in the story?",
            f"The conflict was between {hero.label}'s pride and the wiser advice to stop for a short rest. "
            f"{hero.pronoun().capitalize()} wanted to prove {hero.pronoun()} was strong, but the work needed care more than bragging."
        ),
        (
            f"What did {hero.label} think to {hero.pronoun('object')}self before the mistake?",
            f"{hero.pronoun().capitalize()} told {hero.pronoun('object')}self that stopping would feel like losing. "
            f"That inner monologue is what pushed {hero.pronoun('object')} to ignore the warning."
        ),
        (
            f"What went wrong when {hero.label} kept working without rest?",
            f"{job.mistake} The mistake happened because {hero.pronoun()} kept going after the strain had already started to blur or wobble the work."
        ),
        (
            f"How did {hero.label} fix the problem?",
            f"{hero.pronoun().capitalize()} took {rest_kind.phrase} and came back steadier. "
            f"After that, {job.fix}."
        ),
        (
            "What lesson did the story teach?",
            f"The lesson was that rest is not the same as giving up. A short, sensible break can help someone do a big job better and more carefully."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"catalog", "rest"} | set(f["job"].tags) | set(f["rest_kind"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_rest(R) :- rest_kind(R), sense(R,S), sense_min(M), S >= M.
compatible(J,R)  :- job(J), rest_kind(R), strain_of(J,St), soothes(R,St).
valid(S,J,R,M)   :- setting(S), job(J), rest_kind(R), mood(M), sensible_rest(R), compatible(J,R).
will_mixup(J)    :- job(J).
resolved(J,R)    :- compatible(J,R), sensible_rest(R).
#show valid/4.
#show sensible_rest/1.
#show compatible/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for jid, job in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("strain_of", jid, job.strain))
    for rid, rest_kind in REST_KINDS.items():
        lines.append(asp.fact("rest_kind", rid))
        lines.append(asp.fact("sense", rid, rest_kind.sense))
        for strain in sorted(rest_kind.soothes):
            lines.append(asp.fact("soothes", rid, strain))
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rests() -> list[str]:
    import asp

    model = asp.one_model(asp_program(show="#show sensible_rest/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_rest"))


def asp_compatible_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


CURATED = [
    StoryParams(
        setting="prairie_depot",
        job="seed_packets",
        rest_kind="water_break",
        mood="stubborn",
        name="Molly",
        gender="girl",
        helper="uncle",
        seed=None,
    ),
    StoryParams(
        setting="river_wharf",
        job="boot_orders",
        rest_kind="bench_break",
        mood="proud",
        name="Eli",
        gender="boy",
        helper="aunt",
        seed=None,
    ),
    StoryParams(
        setting="mesa_storehouse",
        job="peach_crate",
        rest_kind="shade_break",
        mood="hasty",
        name="June",
        gender="girl",
        helper="father",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant catalog, a child who refuses rest, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--rest_kind", choices=REST_KINDS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the inline ASP model")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.job and args.rest_kind:
        job = JOBS[args.job]
        rest_kind = REST_KINDS[args.rest_kind]
        if not (compatible_rest(job, rest_kind) and rest_kind.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(job, rest_kind))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.job is None or combo[1] == args.job)
        and (args.rest_kind is None or combo[2] == args.rest_kind)
        and (args.mood is None or combo[3] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, job_id, rest_id, mood_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        setting=setting_id,
        job=job_id,
        rest_kind=rest_id,
        mood=mood_id,
        name=name,
        gender=gender,
        helper=helper,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        base_job = JOBS[params.job]
        rest_kind = REST_KINDS[params.rest_kind]
        mood = MOODS[params.mood]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not (compatible_rest(base_job, rest_kind) and rest_kind.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(base_job, rest_kind))

    job = _job_text(base_job, params.name)
    world = tell(
        setting=setting,
        job=job,
        rest_kind=rest_kind,
        mood=mood,
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper,
    )
    world.get("hero").label = params.name

    story = world.render().replace("hero", params.name)
    return StorySample(
        params=params,
        story=story,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_rests()}
    asp_sensible = set(asp_sensible_rests())
    if py_sensible == asp_sensible:
        print(f"OK: sensible rests match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rests: asp={sorted(asp_sensible)} python={sorted(py_sensible)}")

    py_pairs = {(job.id, rest.id) for job in JOBS.values() for rest in REST_KINDS.values() if compatible_rest(job, rest)}
    asp_pairs = set(asp_compatible_pairs())
    if py_pairs == asp_pairs:
        print(f"OK: compatible job/rest pairs match ({len(py_pairs)} pairs).")
    else:
        rc = 1
        print("MISMATCH in compatible pairs:")
        if asp_pairs - py_pairs:
            print("  only in ASP:", sorted(asp_pairs - py_pairs))
        if py_pairs - asp_pairs:
            print("  only in Python:", sorted(py_pairs - asp_pairs))

    try:
        parser = build_parser()
        smoke_params = resolve_params(parser.parse_args([]), random.Random(0))
        smoke_params.seed = 0
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story or "catalog" not in smoke_sample.story.lower() or "rest" not in smoke_sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing required words or text.)")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story:
                raise StoryError("(Curated sample rendered empty story.)")
        except Exception as err:
            rc = 1
            print(f"CURATED SAMPLE FAILED: {params} -> {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4.\n#show sensible_rest/1.\n#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible rests: {', '.join(asp_sensible_rests())}\n")
        print(f"{len(combos)} compatible (setting, job, rest_kind, mood) combos:\n")
        for setting_id, job_id, rest_id, mood_id in combos:
            print(f"  {setting_id:15} {job_id:13} {rest_id:12} {mood_id}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.job} at {p.setting} ({p.rest_kind}, {p.mood})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
