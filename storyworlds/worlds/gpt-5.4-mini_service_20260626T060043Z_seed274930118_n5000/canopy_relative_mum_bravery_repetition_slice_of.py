#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/canopy_relative_mum_bravery_repetition_slice_of.py
================================================================================================

A small slice-of-life storyworld about a child, a canopy, a visiting relative,
and the quiet kind of bravery that grows through repetition.

Premise:
A child and their mum spend an ordinary day under a garden canopy when a relative
arrives. The child feels shy at first, but a repeated little task gives them
enough courage to help welcome the guest, steady the canopy, and take part in the
day.

The domain is intentionally small and grounded:
- physical meters track things like wind, dampness, and steadiness
- emotional memes track things like shyness, bravery, warmth, and calm
- repeated practice can grow bravery
- a light problem (gusts under the canopy, an awkward welcome, a small task)
  turns into a gentle resolution

This file is standalone and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    under: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["wind", "damp", "steady", "task", "comfort", "mess"]:
            self.meters.setdefault(k, 0.0)
        for k in ["shy", "brave", "warm", "calm", "proud", "tired"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mum", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False


@dataclass
class Task:
    id: str
    verb: str
    repeat_verb: str
    repeated_phrase: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _windy(world: World) -> list[str]:
    out = []
    if world.weather != "windy":
        return out
    for e in world.entities.values():
        if e.id == "canopy":
            continue
        if e.under == "canopy":
            sig = ("windy", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["damp"] += 0.5
            e.meters["mess"] += 0.2
            out.append(f"A few loose drops tapped {e.label or e.id} under the canopy.")
    return out


def _repetition(world: World) -> list[str]:
    out = []
    child = world.get("child")
    task = world.facts.get("task")
    if not task:
        return out
    if child.meters["task"] >= 3 and child.memes["brave"] < 2:
        sig = ("repeat", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["brave"] += 1
            child.memes["shy"] = max(0.0, child.memes["shy"] - 0.5)
            out.append("Doing it again made the job feel smaller and kinder.")
    return out


def _help_relative(world: World) -> list[str]:
    out = []
    child = world.get("child")
    mum = world.get("mum")
    rel = world.get("relative")
    canopy = world.get("canopy")
    if child.memes["brave"] >= THRESHOLD and canopy.meters["steady"] < 1.0:
        sig = ("help", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            canopy.meters["steady"] += 1
            child.memes["proud"] += 1
            mum.memes["warm"] += 1
            rel.memes["warm"] += 1
            out.append(f"{child.id} held the pole with {mum.label} and made the canopy steadier.")
    return out


CAUSAL_RULES = [_windy, _repetition, _help_relative]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world(setting: Setting, task: Task, need: Need, aid: Aid, weather: str, child_name: str, child_type: str, relative_type: str) -> World:
    world = World(setting)
    world.weather = weather
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, traits=["little", "careful"]))
    mum = world.add(Entity(id="mum", kind="character", type="mum", label="mum"))
    relative = world.add(Entity(id="relative", kind="character", type=relative_type, label="relative"))
    canopy = world.add(Entity(id="canopy", type="canopy", label="the canopy", phrase="a striped garden canopy"))
    tasker = world.add(Entity(id="task", type="task", label=task.verb, phrase=task.repeated_phrase))

    child.under = "canopy"
    mum.under = "canopy"
    relative.under = "canopy"
    canopy.meters["steady"] = 0.5
    world.facts.update(task=task, need=need, aid=aid, child=child, mum=mum, relative=relative, canopy=canopy)
    return world


def tell(world: World) -> World:
    child = world.get("child")
    mum = world.get("mum")
    relative = world.get("relative")
    canopy = world.get("canopy")
    task: Task = world.facts["task"]
    need: Need = world.facts["need"]
    aid: Aid = world.facts["aid"]

    child.memes["shy"] += 1
    world.say(f"{child.label} liked the quiet backyard and the striped canopy that made a cool patch of shade.")
    world.say(f"{child.label}'s mum asked for a small hand with {task.repeated_phrase}, and {child.label} agreed to try.")
    world.say(f"That morning, a {relative.type} relative came by for tea and a chat, carrying {need.phrase}.")
    world.para()

    world.say(f"The wind nudged the canopy, and {child.label} felt a little shy about helping while someone was watching.")
    world.say(f"But {task.repeat_verb} helped. {child.label} did it once, then again, then again, each time a little steadier.")
    child.meters["task"] += 3
    child.memes["brave"] += 0.5
    propagate(world, narrate=True)

    world.para()
    world.say(f"When the last knot looked neat, {child.label} lifted the edge of {aid.label} and held it with both hands.")
    world.say(f"{child.label}'s mum smiled because the canopy stayed up, the tea stayed dry, and the little job was finished together.")
    child.memes["warm"] += 1
    child.memes["proud"] += 1
    world.facts["done"] = True
    return world


SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False),
    "garden": Setting(place="the garden", indoor=False),
    "courtyard": Setting(place="the courtyard", indoor=False),
}

TASKS = {
    "tidy_cloth": Task(
        id="tidy_cloth",
        verb="smooth the tablecloth",
        repeat_verb="smoothing the tablecloth",
        repeated_phrase="the tablecloth for tea",
        reward="a neat table",
        tags={"canopy", "repetition", "slice_of_life"},
    ),
    "stack_chairs": Task(
        id="stack_chairs",
        verb="stack the small chairs",
        repeat_verb="stacking the small chairs",
        repeated_phrase="the little chairs by the wall",
        reward="more space",
        tags={"canopy", "repetition"},
    ),
    "pin_notes": Task(
        id="pin_notes",
        verb="pin the paper notes",
        repeat_verb="pinning the paper notes",
        repeated_phrase="the paper notes on the board",
        reward="a tidy display",
        tags={"canopy", "repetition"},
    ),
}

NEEDS = {
    "lemonade": Need(id="lemonade", label="lemonade", phrase="a jug of lemonade", type="drink"),
    "flowers": Need(id="flowers", label="flowers", phrase="a bunch of flowers", type="gift"),
    "blanket": Need(id="blanket", label="blanket", phrase="a folded blanket", type="thing"),
}

AIDS = {
    "peg": Aid(id="peg", label="a wooden peg", phrase="a small wooden peg", helps={"task"}),
    "clothespin": Aid(id="clothespin", label="a clothespin", phrase="a bright clothespin", helps={"task"}),
    "stone": Aid(id="stone", label="a smooth stone", phrase="a smooth stone to weigh the cloth", helps={"task"}),
}

CHILD_NAMES = ["Mina", "Niko", "Rae", "Owen", "Ivy", "June", "Pip", "Noa"]
RELATIVE_TYPES = ["aunt", "uncle", "grandma", "grandpa", "cousin"]
TASK_ORDER = ["tidy_cloth", "stack_chairs", "pin_notes"]


@dataclass
class StoryParams:
    setting: str
    task: str
    need: str
    aid: str
    child_name: str
    child_type: str
    relative_type: str
    weather: str = "windy"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: canopy, relative, mum, bravery, repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--relative-type", choices=RELATIVE_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(TASK_ORDER)
    need = args.need or rng.choice(list(NEEDS))
    aid = args.aid or rng.choice(list(AIDS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    relative_type = args.relative_type or rng.choice(RELATIVE_TYPES)
    return StoryParams(setting, task, need, aid, child_name, child_type, relative_type, seed=args.seed)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life story about a child, a canopy, and a visiting relative.',
        f"Tell a gentle story where {f['child'].label} helps {f['mum'].label} under the canopy while a {f['relative'].type} relative visits.",
        f"Write a small story about bravery that grows through repetition during {f['task'].repeated_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mum = f["mum"]
    relative = f["relative"]
    task: Task = f["task"]
    need: Need = f["need"]
    return [
        QAItem(
            question=f"Who helped {mum.label} under the canopy?",
            answer=f"{child.label} helped {mum.label} under the canopy.",
        ),
        QAItem(
            question=f"Why did {child.label} get braver during the story?",
            answer=f"{child.label} got braver because doing {task.repeat_verb} again and again made the job feel easier.",
        ),
        QAItem(
            question=f"What did the visiting {relative.type} bring?",
            answer=f"The visiting {relative.type} brought {need.phrase}.",
        ),
        QAItem(
            question=f"What stayed steady by the end?",
            answer=f"The canopy stayed steady by the end, and the little tea-time job was finished together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "canopy": [("What is a canopy?", "A canopy is a cover that gives shade or shelter from sun or light rain.")],
    "relative": [("What is a relative?", "A relative is a person in your family, like an aunt, uncle, grandma, grandpa, or cousin.")],
    "mum": [("Who is a mum?", "A mum is a mother, someone who often cares for and helps a child.")],
    "bravery": [("What is bravery?", "Bravery is feeling afraid or unsure and still doing the helpful thing.")],
    "repetition": [("What is repetition?", "Repetition means doing the same thing again and again, which can help you learn or get better at it.")],
    "slice_of_life": [("What is slice-of-life?", "A slice-of-life story shows a small, ordinary moment from everyday life.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for key in ["canopy", "relative", "mum", "bravery", "repetition", "slice_of_life"] for q, a in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.under:
            bits.append(f"under={e.under}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
brave(X) :- brave_raw(X), not blocked(X).
blocked(X) :- shy(X), not helped(X).

helped(child) :- repetition(child).
repetition(child) :- task_done(3).

steady(canopy) :- steady_raw(canopy), not wind_breaks(canopy).
wind_breaks(canopy) :- windy, under(child, canopy), not steady(canopy).

good_story :- brave(child), steady(canopy), warm(mum).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = setup_world(
        SETTINGS[params.setting],
        TASKS[params.task],
        NEEDS[params.need],
        AIDS[params.aid],
        params.weather,
        params.child_name,
        params.child_type,
        params.relative_type,
    )
    tell(world)
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
    StoryParams(setting="backyard", task="tidy_cloth", need="lemonade", aid="peg", child_name="Mina", child_type="girl", relative_type="aunt"),
    StoryParams(setting="garden", task="stack_chairs", need="flowers", aid="stone", child_name="Owen", child_type="boy", relative_type="uncle"),
    StoryParams(setting="courtyard", task="pin_notes", need="blanket", aid="clothespin", child_name="Ivy", child_type="girl", relative_type="grandma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
