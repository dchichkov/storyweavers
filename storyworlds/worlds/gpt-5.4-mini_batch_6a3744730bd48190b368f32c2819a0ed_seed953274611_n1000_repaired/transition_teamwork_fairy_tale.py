#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini/transition_teamwork_fairy_tale.py
===================================================================

A standalone story world for a small fairy-tale domain about a difficult
transition, teamwork, and a gentle, child-facing ending.

Premise:
- A young heir must cross from an old way of doing things into a new one:
  a bridge between two sides of the kingdom is broken, and the castle's lantern
  garden cannot be reached unless the team works together.
- The story tracks physical state in meters and emotional state in memes.
- The team may succeed by cooperating, building, carrying, and opening the way.

The world is intentionally small and constraint-checked. It generates only
plausible story variants with a clear setup, a turn, and a resolution image that
proves something changed.

Contract notes:
- stdlib only in this file
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- supports --qa, --json, --trace, --asp, --verify, --show-asp, --all, -n, --seed
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TEAM_MIN = 2.0


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
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
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
    old_side: str
    new_side: str
    feature: str
    mood: str
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
    verb_ing: str
    need: str
    obstacle: str
    requires: set[str]
    fixed_by: str
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
class Tool:
    id: str
    label: str
    phrase: str
    grants: set[str]
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
class Ally:
    id: str
    type: str
    label: str
    role: str
    gift: str
    traits: list[str] = field(default_factory=list)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "castle": Setting(
        id="castle",
        place="the castle garden",
        old_side="the old tower",
        new_side="the sunlit gate",
        feature="transition",
        mood="fairy-tale bright",
    ),
    "bridge": Setting(
        id="bridge",
        place="the moon bridge",
        old_side="the mossy bank",
        new_side="the lily bank",
        feature="transition",
        mood="moonlit",
    ),
    "forest": Setting(
        id="forest",
        place="the edge of the enchanted forest",
        old_side="the stumpy path",
        new_side="the silver clearing",
        feature="transition",
        mood="soft and green",
    ),
}

TASKS = {
    "carry_stones": Task(
        id="carry_stones",
        verb="carry the stones",
        verb_ing="carrying stones",
        need="a stronger path",
        obstacle="the broken stepping stones",
        requires={"carry"},
        fixed_by="a shared load",
        tags={"stones", "build"},
    ),
    "pull_rope": Task(
        id="pull_rope",
        verb="pull the rope",
        verb_ing="pulling the rope",
        need="a raised gate",
        obstacle="the stuck gate",
        requires={"pull", "help"},
        fixed_by="together at once",
        tags={"rope", "help"},
    ),
    "guide_lantern": Task(
        id="guide_lantern",
        verb="guide the lantern",
        verb_ing="guiding the lantern",
        need="a safe way through dark steps",
        obstacle="the dark stairs",
        requires={"light", "guide"},
        fixed_by="shared light",
        tags={"lantern", "light"},
    ),
}

TOOLS = {
    "plank": Tool(
        id="plank",
        label="a long plank",
        phrase="a long plank",
        grants={"carry", "build"},
        tags={"plank", "build"},
    ),
    "rope": Tool(
        id="rope",
        label="a bright rope",
        phrase="a bright rope",
        grants={"pull", "help"},
        tags={"rope", "help"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a golden lantern",
        phrase="a golden lantern",
        grants={"light", "guide"},
        tags={"lantern", "light"},
    ),
}

ALLIES = {
    "mason": Ally("mason", "woman", "the mason", "helper", "set of stones", ["steady"], {"build"}),
    "page": Ally("page", "boy", "the page", "helper", "bright rope", ["quick"], {"help"}),
    "bird": Ally("bird", "thing", "the little owl", "helper", "lantern song", ["watchful"], {"light"}),
}

GIRL_NAMES = ["Ella", "Mira", "Nina", "Rosa", "Tessa"]
BOY_NAMES = ["Finn", "Gavin", "Hugo", "Otto", "Perrin"]


@dataclass
class StoryParams:
    setting: str
    task: str
    tool1: str
    tool2: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    ruler: str
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if task.id == "pull_rope" and sid == "forest":
                continue
            if task.id == "guide_lantern" and sid == "castle":
                out.append((sid, tid))
            elif task.id == "carry_stones" and sid in {"castle", "bridge"}:
                out.append((sid, tid))
    return out


def task_possible(setting: Setting, task: Task) -> bool:
    return (setting.id, task.id) in set(valid_combos())


def tell(setting: Setting, task: Task, tool1: Tool, tool2: Tool, hero_name: str,
         hero_type: str, helper_name: str, helper_type: str, ruler: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    ruler_ent = world.add(Entity(id="ruler", kind="character", type="queen", label=f"the {ruler}", role="ruler"))
    path = world.add(Entity(id="path", type="path", label=setting.place))
    obstacle = world.add(Entity(id="obstacle", type="thing", label=task.obstacle))
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once in {setting.place}, {hero.id} lived beneath a sky that was "
        f"{setting.mood}. Beyond {setting.old_side} waited {setting.new_side}, "
        f"and the kingdom needed a {setting.feature} from one side to the other."
    )
    world.say(
        f"But {task.obstacle} blocked the way, so {hero.id} could not simply "
        f"{task.verb} without help."
    )
    world.para()
    hero.memes["want"] += 1
    helper.memes["team"] += 1
    world.say(
        f'"I want to {task.verb}," said {hero.id}. "{helper.id}, will you help me '
        f'find a way?"'
    )
    world.say(
        f"{helper.id} nodded and brought {tool1.phrase} and {tool2.phrase}, because "
        f"the task needed more than one pair of hands."
    )
    if task.id == "carry_stones":
        hero.meters["weight"] += 1
        helper.meters["weight"] += 1
        world.say(
            f"Together they lifted stone after stone. {hero.id} carried one end of "
            f"{tool1.phrase}, while {helper.id} balanced the other end, and the path "
            f"grew straight and sure."
        )
        path.meters["strength"] += 2
    elif task.id == "pull_rope":
        world.say(
            f"They tied {tool1.phrase} to the stuck gate and pulled together. "
            f"One tug was not enough, but two brave pulls made the gate creak, then "
            f"swing wide."
        )
        path.meters["open"] += 2
    else:
        world.say(
            f"They carried {tool2.phrase} down the dark steps. {hero.id} held the "
            f"light high, and {helper.id} watched every tread so nobody slipped."
        )
        path.meters["lit"] += 2
    world.para()
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    ruler_ent.memes["pride"] += 1
    world.say(
        f"At last, the {setting.feature} was complete. {hero.id} and {helper.id} "
        f"crossed to {setting.new_side}, where {ruler_ent.label} smiled to see the "
        f"old problem become a new beginning."
    )
    world.say(
        f"That evening the lanterns glowed, the stones stayed steady, and the "
        f"friends laughed because the whole transition had been made with teamwork."
    )
    world.facts.update(
        setting=setting,
        task=task,
        tool1=tool1,
        tool2=tool2,
        hero=hero,
        helper=helper,
        ruler=ruler_ent,
        path=path,
        obstacle=obstacle,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the word "transition" and shows teamwork in {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} work together to solve a {f['task'].id} problem.",
        f'Write a child-friendly fairy tale about an old way becoming a new way, and make the ending feel warm and proud.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id} in {setting.place}. They work together to make a hard transition feel safe and kind."),
        ("What problem did they need to solve?",
         f"They needed to handle {task.obstacle}. It blocked the way, so they had to use teamwork instead of doing it alone."),
        ("How did they solve it?",
         f"They used {f['tool1'].phrase} and {f['tool2'].phrase} together. Each one helped a little, and together they made the way open."),
        ("What changed by the end?",
         f"The old problem was no longer in the way, and {setting.new_side} could be reached. The kingdom moved from stuck to open because they worked as a team."),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "transition": [("What does transition mean?",
                   "A transition is a change from one state or place to another. In stories, it can mean moving from an old problem to a new solution.")],
    "teamwork": [("What is teamwork?",
                 "Teamwork means people help each other and do a task together. When they share the work, hard jobs become easier.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that helps people see in the dark. In fairy tales it often glows softly like a treasure.")],
    "bridge": [("Why do bridges matter?",
                "A bridge helps people cross from one side to another. It connects places that would be hard to reach otherwise.")],
    "stones": [("Why can stones make a path?",
                 "Stones can be placed in a row to make a steady path. If they are set well, people can walk across them safely.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["task"].tags)
    tags.add("teamwork")
    tags.add("transition")
    if f["task"].id == "guide_lantern":
        tags.add("lantern")
    if f["task"].id == "carry_stones":
        tags.add("stones")
    out = []
    for tag, qa in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(qa)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def aspirational_combo_ok(params: StoryParams) -> bool:
    return (params.setting, params.task) in valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.task:
        if not aspirational_combo_ok(StoryParams(
            setting=args.setting,
            task=args.task,
            tool1="plank",
            tool2="rope",
            hero="",
            hero_type="girl",
            helper="",
            helper_type="boy",
            ruler="queen",
        )):
            raise StoryError("(No story: that setting and task do not fit together.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, task_id = rng.choice(sorted(combos))
    task = TASKS[task_id]
    setting = SETTINGS[setting_id]
    if task_id == "carry_stones":
        tool_pair = ("plank", "rope")
    elif task_id == "pull_rope":
        tool_pair = ("rope", "lantern")
    else:
        tool_pair = ("lantern", "rope")
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if helper == hero:
        helper = helper + "a"
    return StoryParams(
        setting=setting_id,
        task=task_id,
        tool1=tool_pair[0],
        tool2=tool_pair[1],
        hero=hero,
        hero_type=gender,
        helper=helper,
        helper_type="boy" if gender == "girl" else "girl",
        ruler=args.ruler or "queen",
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS:
        raise StoryError("invalid params")
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        TOOLS[params.tool1],
        TOOLS[params.tool2],
        params.hero,
        params.hero_type,
        params.helper,
        params.helper_type,
        params.ruler,
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


def valid_story_count() -> int:
    return len(valid_combos())


CURATED = [
    StoryParams(
        setting="castle",
        task="carry_stones",
        tool1="plank",
        tool2="rope",
        hero="Ella",
        hero_type="girl",
        helper="Finn",
        helper_type="boy",
        ruler="queen",
        seed=1,
    ),
    StoryParams(
        setting="castle",
        task="guide_lantern",
        tool1="lantern",
        tool2="rope",
        hero="Mira",
        hero_type="girl",
        helper="Hugo",
        helper_type="boy",
        ruler="queen",
        seed=2,
    ),
    StoryParams(
        setting="bridge",
        task="carry_stones",
        tool1="plank",
        tool2="rope",
        hero="Nina",
        hero_type="girl",
        helper="Perrin",
        helper_type="boy",
        ruler="queen",
        seed=3,
    ),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
task(T) :- task_fact(T).
tool(K) :- tool_fact(K).

compatible(S, T) :- setting_fact(S), task_fact(T), valid_pair(S, T).
valid_pair(castle, carry_stones).
valid_pair(castle, guide_lantern).
valid_pair(bridge, carry_stones).
valid_pair(forest, guide_lantern) :- false.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid in TASKS:
        lines.append(asp.fact("task_fact", tid))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool_fact", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP parity failed.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale transition teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--ruler", choices=["queen", "king"], default="queen")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, t in asp_valid_combos():
            print(s, t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} & {p.helper}: {p.setting}/{p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
