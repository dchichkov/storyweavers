#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/essay_mediocre_suspense_sharing_animal_story.py
===============================================================================

A tiny storyworld for an animal-story premise: a small animal must finish a
school essay, feels it is mediocre, gets nervous, and learns to share help.
The simulation tracks physical meters and emotional memes, so the story is
driven by state changes rather than a frozen paragraph with swapped nouns.

Seed words:
- essay
- mediocre

Features:
- Suspense
- Sharing

Style:
- Animal Story
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
SUSPENSE_MIN = 1.0
HELPFUL_MIN = 2


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
        if self.type in {"rabbit", "mouse", "fox", "cat", "dog", "bear", "deer"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Habitat:
    id: str
    label: str
    setting: str
    sounds: str
    hide_spot: str
    safe_spot: str
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
class Task:
    id: str
    topic: str
    noun: str
    pages: int
    difficulty: int
    suspense_gain: int
    helps: bool
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
    gives: str
    share_text: str
    helpfulness: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").meters["worry"] >= SUSPENSE_MIN and ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        world.get("hero").memes["tremble"] += 1
        out.append("__suspense__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["stuck"] >= THRESHOLD and helper.meters["helped"] < THRESHOLD:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["helped"] += 1
            hero.meters["stuck"] = 0
            hero.memes["relief"] += 1
            helper.memes["kindness"] += 1
            out.append("__share__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("share", "social", _r_share)]


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


def predict(world: World, task: Task) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("hero"), task, narrate=False)
    return {"stuck": sim.get("hero").meters["stuck"] >= THRESHOLD,
            "worry": sim.get("hero").meters["worry"]}


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters["worry"] += task.suspense_gain
    hero.meters["pages"] += task.pages
    hero.memes["pressure"] += 1
    propagate(world, narrate=narrate)


def open_story(world: World, hero: Entity, helper: Entity, habitat: Habitat, task: Task) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In {habitat.setting}, {hero.id} the {hero.type} sat by {habitat.hide_spot} "
        f"and stared at {task.noun}. {habitat.sounds}."
    )
    world.say(
        f"{hero.id} had to write an {task.topic} essay, but {hero.pronoun('possessive')} "
        f"first draft looked mediocre."
    )
    world.say(
        f"{helper.id} watched from {habitat.safe_spot}, quiet as a pawprint."
    )


def raise_stakes(world: World, hero: Entity, task: Task, habitat: Habitat) -> None:
    world.say(
        f"The more {hero.id} erased, the messier the page looked. "
        f"Each line felt like it might tear the whole essay apart."
    )
    world.say(
        f"Outside, a twig snapped near {habitat.hide_spot}, and {hero.id}'s ears perked up."
    )


def ask_for_help(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.meters["stuck"] += 1
    world.say(
        f'"This is turning mediocre," {hero.id} whispered. '
        f'"I need help with my essay."'
    )
    world.say(
        f"{helper.id} leaned closer and said, \"We can share the hard part.\""
    )


def share_help(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["trust"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{helper.id} shared {helper.pronoun('possessive')} idea for a better opening, "
        f"and {hero.id} copied the strong sentence into the essay."
    )
    world.say(
        f"Together they checked the middle, and the story suddenly began to breathe."
    )


def finish(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["joy"] += 1
    hero.meters["worry"] = 0
    world.say(
        f"At last, {hero.id} read the essay aloud. It was no longer mediocre."
    )
    world.say(
        f"{helper.id} smiled, and the two animals sat shoulder to shoulder while the paper "
        f"rested neatly between them."
    )


def tell(habitat: Habitat, task: Task, helper_cfg: Helper,
         hero_name: str = "Milo", hero_type: str = "rabbit") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="writer"))
    helper = world.add(Entity(id="helper", kind="character", type="mouse", label=helper_cfg.label, role="friend"))
    paper = world.add(Entity(id="essay", type="thing", label="the essay"))
    world.facts["hero_name"] = hero_name
    world.facts["helper_label"] = helper_cfg.label
    world.facts["task"] = task
    world.facts["habitat"] = habitat
    world.facts["helper_cfg"] = helper_cfg
    world.facts["paper"] = paper

    open_story(world, hero, helper, habitat, task)
    world.para()
    _do_task(world, hero, task)
    raise_stakes(world, hero, task, habitat)
    ask_for_help(world, hero, helper, task)
    share_help(world, hero, helper, task)
    world.para()
    finish(world, hero, helper, task)

    world.facts.update(
        outcome="shared",
        worried=hero.meters["worry"] >= SUSPENSE_MIN,
        helped=helper.meters["helped"] >= THRESHOLD,
    )
    return world


HABITATS = {
    "burrow": Habitat(id="burrow", label="burrow", setting="a snug burrow", sounds="The tunnel hummed with tiny breaths", hide_spot="the root wall", safe_spot="a mossy shelf", tags={"animal", "burrow"}),
    "barn": Habitat(id="barn", label="barn loft", setting="a dusty barn loft", sounds="The rafters creaked softly above", hide_spot="a hay bale", safe_spot="the ladder rail", tags={"animal", "barn"}),
    "garden": Habitat(id="garden", label="garden hedge", setting="a quiet garden", sounds="Leaves rustled like whispers", hide_spot="the hedge corner", safe_spot="a stone step", tags={"animal", "garden"}),
}

TASKS = {
    "forest": Task(id="forest", topic="forest", noun="a forest journal", pages=3, difficulty=2, suspense_gain=1, helps=True, tags={"essay", "forest"}),
    "river": Task(id="river", topic="river", noun="a river essay", pages=4, difficulty=2, suspense_gain=1, helps=True, tags={"essay", "river"}),
    "friendship": Task(id="friendship", topic="friendship", noun="an essay about friendship", pages=4, difficulty=3, suspense_gain=2, helps=True, tags={"essay", "friendship"}),
}

HELPERS = {
    "mouse": Helper(id="mouse", label="Nina the mouse", gives="a pencil tap", share_text="shared a better opening", helpfulness=3, tags={"sharing", "mouse"}),
    "hedgehog": Helper(id="hedgehog", label="Pip the hedgehog", gives="a careful nod", share_text="shared a softer ending", helpfulness=3, tags={"sharing", "hedgehog"}),
    "owl": Helper(id="owl", label="Owen the owl", gives="a wise blink", share_text="shared a clearer middle", helpfulness=4, tags={"sharing", "owl"}),
}

RESPONSES = {
    "slow_down": Response(id="slow_down", sense=3, power=3, text="slid a paw over the page and helped slow the panic", fail="slid a paw over the page, but the worry still raced ahead", tags={"calm"}),
    "share_notes": Response(id="share_notes", sense=4, power=4, text="shared notes and straightened the rough parts of the essay", fail="shared notes, but the essay was already too tangled", tags={"sharing"}),
}

GIRL_NAMES = ["Mina", "Tilly", "Poppy", "Luna"]
BOY_NAMES = ["Milo", "Otis", "Theo", "Ben"]


@dataclass
class StoryParams:
    habitat: str
    task: str
    helper: str
    name: str
    gender: str
    response: str
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


CURATED = [
    StoryParams(habitat="burrow", task="forest", helper="mouse", name="Milo", gender="rabbit", response="share_notes"),
    StoryParams(habitat="barn", task="friendship", helper="hedgehog", name="Tilly", gender="rabbit", response="slow_down"),
    StoryParams(habitat="garden", task="river", helper="owl", name="Poppy", gender="rabbit", response="share_notes"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h, t, k) for h in HABITATS for t in TASKS for k in HELPERS if TASKS[t].helps]


def explain_rejection() -> str:
    return "(No story: the chosen essay setup would not create a meaningful suspense-and-sharing problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: animal essay, suspense, and sharing.")
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["rabbit", "mouse", "fox", "cat", "dog", "bear", "deer"])
    ap.add_argument("--response", choices=RESPONSES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.habitat is None or c[0] == args.habitat)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError(explain_rejection())
    h, t, k = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or "rabbit"
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(habitat=h, task=t, helper=k, name=name, gender=gender, response=response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a child that includes the words "essay" and "mediocre".',
        f"Tell a suspenseful but gentle animal story where {f['hero_name']} feels the essay is mediocre, then shares the problem with a helper.",
        f"Write a short story about sharing help on an essay, with a nervous middle and a bright ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    task: Task = f["task"]
    habitat: Habitat = f["habitat"]
    helper_cfg: Helper = f["helper_cfg"]
    hero_name = f["hero_name"]
    return [
        ("Who is the story about?",
         f"It is about {hero_name}, a small animal who had to write an essay. The story also includes {helper_cfg.label}, who helps with the tricky part."),
        ("Why did the story feel suspenseful?",
         f"{hero_name} worried that the essay was mediocre and might not turn out well. The tension grew when the page felt stuck and the animal had to decide whether to ask for help."),
        ("How did sharing help?",
         f"{helper_cfg.label} shared ideas and helped fix the rough parts of the essay. That turned the lonely worry into teamwork, which made the ending calm and happy."),
        ("What changed by the end?",
         f"At the end, the essay was no longer mediocre. {hero_name} felt relieved in the {habitat.setting}, and the paper was finished neatly with help from a friend."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an essay?",
         "An essay is a piece of writing where someone tells ideas, explains a topic, or shares a small story."),
        ("What does mediocre mean?",
         "Mediocre means only so-so or not very good. It is a word people use when something could be better."),
        ("What does sharing mean?",
         "Sharing means giving some help, time, or things to another person so both can do better together."),
        ("What is suspense?",
         "Suspense is the feeling of worry or excitement when you do not know what will happen next."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(hero) :- worry(hero, W), W >= 1.
shared(hero) :- stuck(hero), helped(helper).
outcome(shared) :- shared(hero).
outcome(suspense) :- worry(hero, W), W >= 1, not shared(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HABITATS:
        lines.append(asp.fact("habitat", hid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for kid in HELPERS:
        lines.append(asp.fact("helper", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        prog = asp_program("#show outcome/1.")
        asp.one_model(prog)
    except Exception as exc:  # pragma: no cover
        print(f"ASP failed: {exc}")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    return 0


def asp_outcomes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def generate(params: StoryParams) -> StorySample:
    if params.habitat not in HABITATS or params.task not in TASKS or params.helper not in HELPERS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(HABITATS[params.habitat], TASKS[params.task], HELPERS[params.helper], hero_name=params.name, hero_type=params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP outcomes:", asp_outcomes())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
