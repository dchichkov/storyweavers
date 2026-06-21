#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/county_granulate_suey_suspense_misunderstanding_heartwarming.py
================================================================================================

A standalone story world for a tiny heartwarming suspense / misunderstanding tale:
a child and a grown-up prepare a county fair dish, a small mix-up makes everyone
worry for a moment, and then the misunderstanding is kindly cleared up.

Seed words:
- county
- granulate
- suey

Style:
- Heartwarming

The simulation tracks:
- a child trying to help with a county fair recipe,
- a granulating step that must be done carefully,
- a suspenseful moment when a label or package is misread as "suey",
- and a warm ending where the grown-up and child fix the mix-up together.

This script follows the Storyweavers storyworld contract and is self-contained.
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
CONFUSION_MIN = 1.0


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

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    county_event: str
    backdrop: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Task:
    id: str
    step: str
    needed: str
    risk: str
    safe_tool: str
    tag: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Package:
    id: str
    label: str
    looks_like: str
    contents: str
    warning: str
    confusing: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    action: str
    comfort: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["confusion"] < CONFUSION_MIN:
        return out
    sig = ("confusion", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["suspense"] += 1
    out.append("__confusion__")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grown = world.get("grownup")
    if child.memes["fear"] < THRESHOLD:
        return out
    sig = ("reassure", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["safe"] += 1
    grown.memes["warmth"] += 1
    out.append("__reassure__")
    return out


CAUSAL_RULES = [Rule("confusion", "social", _r_confusion), Rule("reassure", "social", _r_reassure)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def _do_granulate(world: World, task: Task, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["granulated"] += 1
    child.memes["helpful"] += 1
    propagate(world, narrate=narrate)


def predict_misunderstanding(world: World, package: Package, task: Task) -> dict:
    sim = world.copy()
    _do_granulate(sim, task, narrate=False)
    confusing = package.confusing or "suey" in package.label.lower() or "suey" in package.looks_like.lower()
    if confusing:
        sim.get("child").memes["confusion"] += 1
        propagate(sim, narrate=False)
    return {
        "confused": sim.get("child").memes["confusion"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def begin(world: World, child: Entity, grownup: Entity, setting: Setting, task: Task) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a bright day in the county, {child.id} and {grownup.id} worked at "
        f"{setting.place}. {setting.backdrop}"
    )
    world.say(
        f"They were getting ready for {setting.county_event}, and {child.id} wanted to help "
        f"with the {task.step}."
    )


def explain_task(world: World, child: Entity, grownup: Entity, task: Task) -> None:
    world.say(
        f'"If we do this carefully, the mix will {task.needed}," {grownup.id} said, '
        f"showing {child.pronoun('object')} the bowl."
    )
    world.say(
        f'{child.id} nodded. "{task.safe_tool} sounds important," {child.id} said, '
        f"trying to sound brave."
    )


def introduce_package(world: World, package: Package) -> None:
    world.say(
        f"Then {package.label} came out of the pantry. It looked like {package.looks_like}, "
        f"but it was really for {package.contents}."
    )


def suspense_misread(world: World, child: Entity, package: Package, task: Task) -> None:
    child.memes["fear"] += 1
    child.memes["confusion"] += 1
    world.say(
        f"{child.id} froze for a second. The label was hard to read, and {child.id} thought it "
        f"might say {package.warning}."
    )
    world.say(
        f'That made the kitchen feel very quiet, because "suey" sounded like something that '
        f"did not belong in a county prize recipe."
    )


def clarify(world: World, grownup: Entity, child: Entity, package: Package) -> None:
    child.memes["fear"] = 0
    child.memes["confusion"] = 0
    world.say(
        f"{grownup.id} leaned closer and smiled. "  # noqa: E501
        f'"Oh, sweetie, it does not say suey. It says {package.contents}."'
    )
    world.say(
        f"{child.id} blinked, then laughed in relief. The scary guess was only a misunderstanding."
    )


def finish(world: World, child: Entity, grownup: Entity, helper: Helper, package: Package) -> None:
    child.memes["joy"] += 1
    grownup.memes["joy"] += 1
    world.say(
        f"Together they finished the {helper.action}, and {helper.label} helped {child.id} "
        f"feel calm again."
    )
    world.say(
        f"By the end, the county dish was ready, the kitchen smelled warm and sweet, and "
        f"{child.id} was proud to have helped."
    )
    world.say(
        f"Even the little worry about {package.warning} had turned into a happy laugh."
    )


def tell(setting: Setting, task: Task, package: Package, helper: Helper,
         child_name: str = "Mina", child_gender: str = "girl",
         grown_name: str = "Aunt June", grown_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    grownup = world.add(Entity(id=grown_name, kind="character", type=grown_gender, role="grownup"))
    world.add(Entity(id="task", type="task", label=task.step))
    world.add(Entity(id="package", type="package", label=package.label))

    begin(world, child, grownup, setting, task)
    world.para()
    explain_task(world, child, grownup, task)
    introduce_package(world, package)
    world.para()
    task_state = predict_misunderstanding(world, package, task)
    _do_granulate(world, task)
    if task_state["confused"] or package.confusing:
        suspense_misread(world, child, package, task)
        clarify(world, grownup, child, package)
    else:
        world.say(
            f"{child.id} kept stirring, and the work stayed calm the whole time."
        )
    world.para()
    finish(world, child, grownup, helper, package)
    world.facts.update(
        child=child,
        grownup=grownup,
        setting=setting,
        task=task,
        package=package,
        helper=helper,
        misunderstanding=True,
        suspense=True,
        resolved=True,
    )
    return world


SETTINGS = {
    "county_kitchen": Setting(
        "county_kitchen",
        "the county kitchen",
        "busy and kind",
        "the county fair supper",
        "sunlight on the window and a blue checkered towel on the counter",
    ),
    "county_hall": Setting(
        "county_hall",
        "the county hall kitchen",
        "bright and echoey",
        "the county potluck",
        "paper lanterns hanging over a long table",
    ),
}

TASKS = {
    "granulate": Task(
        "granulate",
        "granulate the sugar",
        "make the sugar fine enough for the recipe",
        "a gritty spoonful would make the dessert uneven",
        "the little sifter",
        tag="granulate",
    ),
    "stir": Task(
        "stir",
        "stir the batter",
        "blend everything smoothly",
        "lumps would make the cake heavy",
        "the wooden spoon",
        tag="mix",
    ),
}

PACKAGES = {
    "sugar_bag": Package(
        "sugar_bag",
        "a paper bag of sugar",
        "a white sack with a curled top",
        "sweet sugar for the county recipe",
        "suey",
        confusing=False,
        tags={"sugar", "county", "suey"},
    ),
    "label_mixed": Package(
        "label_mixed",
        "a label that was hard to read",
        "an old sticker with smudged letters",
        "sweet sugar for the county recipe",
        "suey",
        confusing=True,
        tags={"sugar", "county", "suey"},
    ),
}

HELPERS = {
    "cat": Helper("cat", "the cat", "stirring in the kitchen", "a soft purr", tags={"comfort"}),
    "aunt": Helper("aunt", "Aunt June", "finishing the counting and measuring", "a warm grin", tags={"warmth"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    package: str
    helper: str
    child: str
    child_gender: str
    grown: str
    grown_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for p in PACKAGES:
                if t == "granulate" and p in {"sugar_bag", "label_mixed"}:
                    combos.append((s, t, p))
                if t == "stir" and p == "label_mixed":
                    combos.append((s, t, p))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    package = f["package"]
    return [
        f'Write a heartwarming suspense story set in the county that includes the word "county".',
        f"Tell a gentle story where {child.id} helps {task.step}, but the label on a package makes {child.id} briefly think it says suey.",
        f'Write a story with a small misunderstanding, then a kind explanation, and include the word "{package.warning}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    task = f["task"]
    package = f["package"]
    qa = [
        ("Who was the story about?",
         f"It was about {child.id} and {grownup.id} working together in the county kitchen. "
         f"The story stays close to them so the little suspense feels personal and warm."),
        ("What was {0} trying to do?".format(child.id),
         f"{child.id} was trying to help {task.step}. That made the kitchen feel important because the dish was for the county event."),
        ("Why did {0} get worried?".format(child.id),
         f"{child.id} got worried because the label was hard to read and looked like it might say {package.warning}. "
         f"The worry was only a misunderstanding, but it was enough to make a suspenseful moment."),
        ("How was the misunderstanding fixed?",
         f"{grownup.id} looked again and explained that the package really held sweet sugar for the county recipe. "
         f"Once {child.id} understood that, the fear went away and the work could continue calmly."),
        ("How did the story end?",
         f"It ended with the county dish ready, the kitchen warm and sweet, and {child.id} proud to help. "
         f"That ending shows the worry turned into shared relief."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["package"].tags) | {"county", "sugar"}
    if f["task"].id == "granulate":
        tags.add("granulate")
    out = []
    knowledge = {
        "county": [("What is a county?", "A county is a local area in a state or country. People may hold fairs, meetings, and other community events there.")],
        "granulate": [("What does it mean to granulate something?", "To granulate something means to break it into tiny grains or small pieces. In cooking, it can help sugar become finer or easier to use.")],
        "sugar": [("What is sugar?", "Sugar is a sweet ingredient used in many recipes. It can make baked treats taste sweet and pleasant.")],
        "suey": [("What is 'suey' in this story?", "Here, 'suey' is only a misread word on a label. It is not part of the recipe, which is why the misunderstanding felt surprising.")],
    }
    for key in ["county", "granulate", "sugar", "suey"]:
        if key in tags:
            out.extend(knowledge[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("county_kitchen", "granulate", "sugar_bag", "aunt", "Mina", "girl", "Aunt June", "woman"),
    StoryParams("county_hall", "granulate", "label_mixed", "aunt", "Noah", "boy", "Aunt June", "woman"),
    StoryParams("county_kitchen", "stir", "label_mixed", "cat", "Lia", "girl", "Mom", "woman"),
]


def explain_rejection(task: Task, package: Package) -> str:
    if task.id != "granulate" and package.confusing:
        return "(No story: this setup has no strong suspenseful misunderstanding, so it would not make a good heartwarming tale.)"
    return "(No story: the chosen pieces do not make a clear county kitchen story.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needs", tid, t.needed))
        if tid == "granulate":
            lines.append(asp.fact("is_granulate", tid))
    for pid, p in PACKAGES.items():
        lines.append(asp.fact("package", pid))
        if p.confusing:
            lines.append(asp.fact("confusing", pid))
        if "suey" in p.warning:
            lines.append(asp.fact("suey_hint", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, P) :- setting(S), task(T), package(P), is_granulate(T), suey_hint(P).
valid(S, T, P) :- setting(S), task(T), package(P), confusing(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print(" python-only:", sorted(py - cl))
        print(" asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming county story world with suspense and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--package", choices=PACKAGES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grown", choices=["Mom", "Dad", "Aunt June"])
    ap.add_argument("--grown-gender", choices=["woman", "man"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.package:
        task = TASKS[args.task]
        package = PACKAGES[args.package]
        if not ((task.id == "granulate" and "suey" in package.warning) or package.confusing):
            raise StoryError(explain_rejection(task, package))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.package is None or c[2] == args.package)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, package = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or (rng.choice(["Mina", "Lia", "Nora"]) if child_gender == "girl" else rng.choice(["Noah", "Evan", "Theo"]))
    grown = args.grown or rng.choice(["Mom", "Dad", "Aunt June"])
    grown_gender = args.grown_gender or ("woman" if grown in {"Mom", "Aunt June"} else "man")
    helper = rng.choice(sorted(HELPERS))
    return StoryParams(setting, task, package, helper, child, child_gender, grown, grown_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], PACKAGES[params.package], HELPERS[params.helper],
                 params.child, params.child_gender, params.grown, params.grown_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
