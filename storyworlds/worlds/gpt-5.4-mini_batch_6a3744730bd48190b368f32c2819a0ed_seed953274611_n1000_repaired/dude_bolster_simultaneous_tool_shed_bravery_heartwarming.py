#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dude_bolster_simultaneous_tool_shed_bravery_heartwarming.py
===========================================================================================

A small story world in a tool shed: a cautious kid wants to be brave, a helper
bolsters him, and two simple tasks happen simultaneously. The turn is heartwarming:
the brave choice is not loud or showy, but calm, helpful, and kind.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

BRAVERY_THRESHOLD = 2.0
NEED_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "dude"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    textures: list[str]
    smell: str
    safe_spots: list[str]
    affords: set[str] = field(default_factory=set)
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
    verb: str
    object_phrase: str
    kind_word: str
    requires: str
    simultaneous_partner: str
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
class HelpItem:
    id: str
    label: str
    phrase: str
    bolster_text: str
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
class StoryParams:
    setting: str
    task: str
    bolster: str
    helper: str
    name: str
    name_gender: str
    parent: str
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tool-shed bravery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--bolster", choices=BOOSTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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


SETTINGS = {
    "tool_shed": Setting(
        id="tool_shed",
        label="the tool shed",
        textures=["cool wood", "dusty shelves", "bright hooks"],
        smell="dry wood and metal",
        safe_spots=["the workbench", "the open floor"],
        affords={"fix,care"},
    ),
}

TASKS = {
    "sweep": Task(
        id="sweep",
        verb="sweep",
        object_phrase="the dusty floor",
        kind_word="broom",
        requires="brush",
        simultaneous_partner="sort bolts",
        tags={"dust", "help"},
    ),
    "sort": Task(
        id="sort",
        verb="sort",
        object_phrase="the screws into jars",
        kind_word="jars",
        requires="hands",
        simultaneous_partner="sweep",
        tags={"order", "help"},
    ),
}

BOOSTS = {
    "bolster": HelpItem(
        id="bolster",
        label="a bolster",
        phrase="a soft bolster pillow",
        bolster_text="put a soft bolster pillow behind the stool so the child could reach",
        tags={"bolster", "support"},
    ),
}

HELPERS = {
    "flashlight": HelpItem(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        bolster_text="held a flashlight steady",
        tags={"light"},
    ),
    "stepstool": HelpItem(
        id="stepstool",
        label="step stool",
        phrase="a little step stool",
        bolster_text="set a little step stool by the shelf",
        tags={"support"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Theo", "Noah", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for b in BOOSTS:
                if s == "tool_shed":
                    out.append((s, t, b))
    return out


def maybe_story_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.task in TASKS and params.bolster in BOOSTS and params.helper in HELPERS


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for b in BOOSTS:
        lines.append(asp.fact("bolster", b))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,B) :- setting(S), task(T), bolster(B), S = tool_shed.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    bolster = args.bolster or "bolster"
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mom", "dad"])
    if not maybe_story_reasonable(StoryParams(setting=setting, task=task, bolster=bolster, helper=helper, name=name, name_gender=gender, parent=parent)):
        raise StoryError("This set of choices does not make a reasonable tool-shed story.")
    return StoryParams(setting=setting, task=task, bolster=bolster, helper=helper, name=name, name_gender=gender, parent=parent)


def _apply_simultaneous(world: World, hero: Entity, task: Task) -> None:
    if ("simul", hero.id) in world.fired:
        return
    world.fired.add(("simul", hero.id))
    hero.memes["confidence"] += 1
    world.say(
        f"At the same time, {hero.id} kept {task.verb}ing while the helper {task.simultaneous_partner}."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    bolster = BOOSTS[params.bolster]
    helper = HELPERS[params.helper]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.name_gender, role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", role="parent"))
    hero.memes["bravery"] = 1.0
    hero.memes["worry"] = 1.0
    hero.meters["need"] = 1.0

    world.say(
        f"In {setting.label}, {hero.id} found a quiet job to do. The air smelled of {setting.smell}, and the old shelves stood in a neat row."
    )
    world.say(
        f"{hero.id} wanted to {task.verb} {task.object_phrase}, and {helper.bolster_text}. That made the little task feel manageable."
    )
    world.para()
    world.say(
        f'{"He" if params.name_gender == "boy" else "She"} took a breath and stood taller. "I can do it," {hero.id} said, with brave hands and a soft voice.'
    )
    world.say(
        f"Then {world.get('Parent').label_word} smiled and said that was the right kind of brave: not rushing, just helping."
    )
    _apply_simultaneous(world, hero, task)
    hero.memes["bravery"] += 2
    hero.meters["done"] += 1
    world.para()
    world.say(
        f"Together they finished in one calm stretch: {hero.id} {task.verb}ed {task.object_phrase}, {helper.label_word} stayed in place, and the shed felt bright and tidy."
    )
    world.say(
        f"{hero.id} grinned at the neat little order of it all, and {world.get('Parent').label_word} gave a warm hug."
    )
    world.facts.update(hero=hero, parent=parent, task=task, bolster=bolster, helper=helper, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task = f["hero"], f["task"]
    return [
        f'Write a heartwarming story that includes the words "dude", "bolster", and "simultaneous" in a tool shed.',
        f"Tell a gentle bravery story where {hero.id} is nervous in the tool shed but finds courage with a bolster and a kind helper.",
        f"Write a small, warm story about a tool shed, a brave dude, and two simultaneous jobs that finish together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, task = f["hero"], f["parent"], f["task"]
    return [
        QAItem(
            question="What did the main character do in the tool shed?",
            answer=f"{hero.id} chose to {task.verb} {task.object_phrase} and kept going even though it felt a little scary. The brave part was doing the job calmly instead of giving up."
        ),
        QAItem(
            question="How did the bolster help?",
            answer=f"The bolster gave the work a softer, steadier feeling by making the setup easier and safer. That support helped {hero.id} feel brave enough to continue."
        ),
        QAItem(
            question="What was happening at the same time?",
            answer=f"While {hero.id} worked on {task.verb}ing, the helper was doing {task.simultaneous_partner}. Both jobs happened together, so the tool shed got tidier in one calm stretch."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building or room where people keep tools, jars, boxes, and other things for fixing and building."
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means you do the right thing even if you feel nervous. It can be quiet bravery, like taking a careful breath and trying anyway."
        ),
        QAItem(
            question="What does simultaneous mean?",
            answer="Simultaneous means two things happen at the same time. One person can sweep while another sorts, and both actions are simultaneous."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if not maybe_story_reasonable(params):
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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


CURATED = [
    StoryParams(setting="tool_shed", task="sweep", bolster="bolster", helper="stepstool", name="Ben", name_gender="boy", parent="mom"),
    StoryParams(setting="tool_shed", task="sort", bolster="bolster", helper="flashlight", name="Mia", name_gender="girl", parent="dad"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid combo parity.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print("OK: ASP parity and generate smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
