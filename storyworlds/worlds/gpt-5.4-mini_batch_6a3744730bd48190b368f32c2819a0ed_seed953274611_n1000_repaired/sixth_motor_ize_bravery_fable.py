#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sixth_motor_ize_bravery_fable.py
=================================================================

A small, self-contained story world for a fable-style tale about bravery,
a sixth-day problem, and the choice to motor-ize an old cart the sensible way.

Premise:
- A little village needs a way to haul seed up a steep hill on the sixth market day.
- One character wants to motor-ize the cart, but another worries about noise,
  safety, and whether the hill actually needs that fix.
- Bravery shows up as telling the truth, asking for help, and carrying through
  a careful plan.
- The ending should feel like a fable: a clear lesson, a concrete change, and
  a small bright image of the village afterward.

This file follows the shared Storyweavers contract:
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --show-asp, --asp, --json, --qa, --trace, --all, -n, --seed
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    noisy: bool = False
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "mare"}
        male = {"boy", "father", "man", "brother", "stallion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Setting:
    id: str
    place: str
    hill: str
    mood: str
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
class Device:
    id: str
    label: str
    phrase: str
    power: int
    safe_power: int
    noisy: bool = False
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
class Task:
    id: str
    verb: str
    object_word: str
    risk_word: str
    challenge: str
    needs_bravery: bool
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


@dataclass
class StoryParams:
    setting: str
    task: str
    device: str
    response: str
    hero: str
    helper: str
    mentor: str
    hero_type: str
    helper_type: str
    mentor_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = dict(self.facts)
        return clone


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


def _r_bravery(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["bravery"] >= THRESHOLD and not world.facts.get("lesson_spoken"):
        sig = ("bravery",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__bravery__")
    return out


def _r_noise(world: World) -> list[str]:
    out = []
    device = world.get("device")
    if device.meters["running"] >= THRESHOLD and device.noisy and not world.facts.get("noticed_noise"):
        sig = ("noise",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("village").memes["unease"] += 1
            out.append("__noise__")
    return out


CAUSAL_RULES = [Rule("bravery", _r_bravery), Rule("noise", _r_noise)]


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


def reasonable(setting: Setting, task: Task, device: Device) -> bool:
    return ("hill" in setting.tags and task.needs_bravery and device.safe_power >= 1 and device.power >= 1)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for d in DEVICES:
                if reasonable(SETTINGS[s], TASKS[t], DEVICES[d]):
                    combos.append((s, t, d))
    return combos


def predict(world: World, device: Device) -> dict:
    sim = world.copy()
    sim.get("device").meters["running"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("village").memes["unease"],
        "running": sim.get("device").meters["running"],
    }


def introduce(world: World, hero: Entity, helper: Entity, mentor: Entity, setting: Setting) -> None:
    world.say(
        f"On the sixth market day, {hero.id} and {helper.id} came to {setting.place}. "
        f"{setting.mood.capitalize()}, the road rose toward {setting.hill}."
    )
    world.say(
        f"Old {mentor.id} watched the cart and the sacks of seed. "
        f"The village needed the grain to reach the top before sunset."
    )


def want_fix(world: World, hero: Entity, task: Task, device: Device) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} looked at the cart and said, \"We should motor-ize it.\" "
        f"{hero.pronoun().capitalize()} wanted to {task.verb} {task.object_word} up the hill."
    )
    world.say(
        f"It sounded brave, but {device.label} could make a lot of noise."
    )


def warn(world: World, helper: Entity, mentor: Entity, task: Task, device: Device) -> None:
    pred = predict(world, device)
    helper.memes["care"] += 1
    world.facts["pred_noise"] = pred["noise"]
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip. "
        f"\"If we rush, the cart may rattle, and the hens will scatter,\" "
        f"{helper.pronoun()} said."
    )
    world.say(
        f"{mentor.id} nodded. \"Bravery is not only speed,\" {mentor.pronoun()} said."
    )


def act(world: World, hero: Entity, helper: Entity, task: Task, device: Device) -> None:
    hero.memes["bravery"] += 1
    device.meters["running"] += 1
    world.say(
        f"Still, {hero.id} did not run away from the hard choice. "
        f"{hero.pronoun().capitalize()} helped {helper.id} fit the motor kit to the cart."
    )
    propagate(world, narrate=True)


def settle(world: World, mentor: Entity, hero: Entity, helper: Entity, task: Task, response: Response) -> None:
    world.say(
        f"{mentor.id} came closer and {response.text}."
    )
    world.say(
        f"The cart climbed the hill in a steady hum, and the seed reached the top safely."
    )
    world.say(
        f"{mentor.id} smiled. \"A brave heart also knows when to choose a careful road,\" "
        f"{mentor.pronoun()} said."
    )


def lesson(world: World, mentor: Entity, hero: Entity, helper: Entity) -> None:
    for e in (hero, helper):
        e.memes["pride"] += 1
        e.memes["peace"] += 1
    world.facts["lesson_spoken"] = True
    world.say(
        f"By dusk, the sixth cart sat at the hilltop, and the village lanterns blinked on. "
        f"{hero.id} and {helper.id} had learned that bravery could be loud or quiet, "
        f"but it still had to be wise."
    )


def tell(setting: Setting, task: Task, device: Device, response: Response,
         hero_name: str = "Milo", helper_name: str = "Nia", mentor_name: str = "Tarin",
         hero_type: str = "boy", helper_type: str = "girl", mentor_type: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label=mentor_name, role="mentor"))
    village = world.add(Entity(id="village", type="place", label="the village"))
    cart = world.add(Entity(id="cart", type="thing", label="cart"))
    device_ent = world.add(Entity(id="device", type="device", label=device.label, noisy=device.noisy))
    device_ent.meters["running"] = 0.0

    hero.memes["bravery"] = 2.0
    helper.memes["care"] = 2.0

    introduce(world, world.get("hero"), world.get("helper"), world.get("mentor"), setting)
    world.para()
    want_fix(world, world.get("hero"), task, device)
    warn(world, world.get("helper"), world.get("mentor"), task, device)
    world.para()
    act(world, world.get("hero"), world.get("helper"), task, device)
    settle(world, world.get("mentor"), world.get("hero"), world.get("helper"), task, response)
    world.para()
    lesson(world, world.get("mentor"), world.get("hero"), world.get("helper"))

    world.facts.update(
        setting=setting, task=task, device=device, response=response,
        hero=world.get("hero"), helper=world.get("helper"), mentor=world.get("mentor"),
        cart=cart, village=village,
    )
    return world


SETTINGS = {
    "hill_village": Setting(id="hill_village", place="the hill village", hill="the steep road", mood="On the sixth morning", tags={"hill"}),
    "river_town": Setting(id="river_town", place="the river town", hill="the long bridge hill", mood="By the sixth bell", tags={"hill"}),
}

TASKS = {
    "grain": Task(id="grain", verb="carry", object_word="grain", risk_word="strain", challenge="a steep climb", needs_bravery=True, tags={"burden"}),
    "milk": Task(id="milk", verb="deliver", object_word="milk jars", risk_word="spill", challenge="a wobbly climb", needs_bravery=True, tags={"burden"}),
}

DEVICES = {
    "small_motor": Device(id="small_motor", label="a small motor kit", phrase="a small motor kit", power=2, safe_power=2, noisy=True, tags={"motor"}),
    "quiet_motor": Device(id="quiet_motor", label="a quiet motor", phrase="a quiet motor", power=3, safe_power=3, noisy=False, tags={"motor"}),
    "wind_winch": Device(id="wind_winch", label="a wind-winch", phrase="a wind-winch", power=2, safe_power=2, noisy=False, tags={"motor"}),
}

RESPONSES = {
    "steady": Response(id="steady", sense=3, power=3,
                       text="showed them how to fasten the harness straight, check the bolts, and keep the cart steady",
                       fail="tried to hurry the work, but the cart jolted and the seed bags slipped",
                       qa_text="showed them how to fasten the harness straight and keep the cart steady",
                       tags={"wise"}),
    "quiet_help": Response(id="quiet_help", sense=2, power=2,
                           text="helped them choose the quiet motor and reminded them to move slowly",
                           fail="helped, but the machine still rattled too much",
                           qa_text="helped them choose the quiet motor and move slowly",
                           tags={"wise"}),
}

GREETINGS = ["Milo", "Lina", "Tessa", "Oren", "Mira", "Jori", "Pippa", "Rafi"]
HELPERS = ["Nia", "Bram", "Suri", "Jude", "Mina", "Perrin"]
MENTORS = ["Tarin", "Edda", "Marlo", "Hana"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child about bravery that includes the words "sixth" and "motor-ize".',
        f"Tell a short story where {f['hero'].label_word} wants to motor-ize a cart on the sixth market day, but learns bravery must be wise.",
        f"Write a gentle village fable about a steep hill, a careful helper, and a brave plan for the cart.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mentor = f["mentor"]
    task = f["task"]
    response = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {hero.label_word}, {helper.label_word}, and {mentor.label_word} in a village that needed help on the sixth market day."),
        ("What did the hero want to do?",
         f"{hero.label_word} wanted to motor-ize the cart so the village could carry {task.object_word} up the hill more easily."),
        ("Why did the helper worry?",
         f"{helper.label_word} worried that the machine might be noisy and clumsy. That mattered because the cart had to climb a steep road without losing its load."),
        ("How did the mentor respond?",
         f"{mentor.label_word} answered with a calm, wise plan and helped them use the machine carefully. The mentor's help turned the brave idea into a safe one."),
        ("What changed by the end?",
         f"The cart reached the hilltop, the seed arrived safely, and the children learned that bravery is strongest when it is thoughtful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does bravery mean in a fable?",
         "Bravery means doing what is right even when it feels hard or scary. In a fable, bravery often includes thinking carefully instead of rushing."),
        ("What does motor-ize mean?",
         "Motor-ize means to add a motor so something can move with machine power instead of only by hand or muscle."),
        ("Why can a hill be hard for a cart?",
         "A hill is hard because carts must climb upward, and heavy things can roll back or get stuck if the path is steep."),
    ]


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
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="hill_village", task="grain", device="quiet_motor", response="steady",
                hero="Milo", helper="Nia", mentor="Tarin", hero_type="boy",
                helper_type="girl", mentor_type="man"),
    StoryParams(setting="river_town", task="milk", device="small_motor", response="quiet_help",
                hero="Lina", helper="Bram", mentor="Edda", hero_type="girl",
                helper_type="boy", mentor_type="woman"),
]


def explain_rejection(setting: Setting, task: Task, device: Device) -> str:
    return "(No story: this village task is not a good fit for a fable-like motor-ize solution.)"


def valid_params(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.task in TASKS and params.device in DEVICES and params.response in RESPONSES


def outcome_of(params: StoryParams) -> str:
    return "wise"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    task = args.task or rng.choice(sorted(TASKS))
    device = args.device or rng.choice(sorted(DEVICES))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.hero or rng.choice(GREETINGS)
    helper = args.helper or rng.choice(HELPERS)
    mentor = args.mentor or rng.choice(MENTORS)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or ("girl" if hero_type == "boy" else "boy")
    mentor_type = args.mentor_type or rng.choice(["man", "woman"])
    params = StoryParams(setting=setting, task=task, device=device, response=response,
                         hero=hero, helper=helper, mentor=mentor,
                         hero_type=hero_type, helper_type=helper_type, mentor_type=mentor_type)
    if not valid_params(params):
        raise StoryError("(Invalid story parameters.)")
    return params


def generate(params: StoryParams) -> StorySample:
    for field_name in ("setting", "task", "device", "response"):
        if getattr(params, field_name) not in globals()[field_name.upper() + "S"]:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(
        SETTINGS[params.setting], TASKS[params.task], DEVICES[params.device], RESPONSES[params.response],
        hero_name=params.hero, helper_name=params.helper, mentor_name=params.mentor,
        hero_type=params.hero_type, helper_type=params.helper_type, mentor_type=params.mentor_type,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about bravery and a motor-ized cart.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--mentor")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-type", choices=["boy", "girl"])
    ap.add_argument("--mentor-type", choices=["man", "woman"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needs_bravery", tid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,D) :- setting(S), task(T), device(D), needs_bravery(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP parity failed.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True, trace=True)
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
