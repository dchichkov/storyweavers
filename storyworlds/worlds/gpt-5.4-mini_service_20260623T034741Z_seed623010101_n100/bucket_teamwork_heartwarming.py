#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/bucket_teamwork_heartwarming.py
==============================================================================================================

A small heartwarming storyworld about teamwork with a bucket.

Premise:
- A child notices something in the garden needs help.
- The bucket is too heavy or the task is too hard alone.
- A helper joins in, and they solve it together.
- The ending proves the change in the world: the plant is revived, the bucket is put away, and everyone feels proud and close.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py only inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
- three QA sets generated from world state, not by parsing rendered English
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
    role: str = ""
    plural: bool = False
    owner: str = ""
    caretaker: str = ""
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    has_water_source: bool = True
    has_garden: bool = True


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    need: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
class StoryParams:
    place: str
    task: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", has_water_source=True, has_garden=True),
    "backyard": Setting(place="the backyard", has_water_source=True, has_garden=True),
    "community_garden": Setting(place="the community garden", has_water_source=True, has_garden=True),
    "porch": Setting(place="the porch", has_water_source=True, has_garden=False),
}

TASKS = {
    "water_flower": Task(
        id="water_flower",
        verb="water the flower bed",
        gerund="watering the flower bed",
        need="water",
        result="the flowers perked up",
        tags={"water", "garden", "gentle"},
    ),
    "fill_birdbath": Task(
        id="fill_birdbath",
        verb="fill the birdbath",
        gerund="filling the birdbath",
        need="water",
        result="the birds had a fresh place to drink",
        tags={"water", "birds", "garden"},
    ),
    "wash_seedlings": Task(
        id="wash_seedlings",
        verb="rinse the dusty seedlings",
        gerund="rinsing the dusty seedlings",
        need="water",
        result="the little green leaves looked brighter",
        tags={"water", "garden", "care"},
    ),
}

BUCKET = Tool(id="bucket", label="bucket", phrase="a sturdy bucket", tags={"bucket", "water"})


def valid_combos() -> list[tuple[str, str]]:
    return [(place, task) for place, s in SETTINGS.items() if s.has_water_source and s.has_garden for task in TASKS]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_fill(world: World) -> list[str]:
    out = []
    child = world.get("child")
    bucket = world.get("bucket")
    if bucket.meters.get("empty", 0) >= THRESHOLD and world.facts.get("at_water_source") and "filled" not in world.fired:
        world.fired.add(("filled",))
        bucket.meters["water"] = 1.0
        bucket.meters["empty"] = 0.0
        child.memes["helpful"] += 1
        out.append("__filled__")
    return out


def _r_shared_lift(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    bucket = world.get("bucket")
    if bucket.meters.get("heavy", 0) >= THRESHOLD and child.memes.get("asking", 0) >= THRESHOLD and helper.memes.get("willing", 0) >= THRESHOLD:
        sig = ("shared_lift",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bucket.meters["steady"] = 1.0
        child.memes["relief"] += 1
        helper.memes["pride"] += 1
        out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("fill", _r_fill), Rule("shared_lift", _r_shared_lift)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def task_at_risk(task: Task) -> bool:
    return "water" in task.tags


def select_helper(task: Task) -> bool:
    return task_at_risk(task)


def reasonableness_gate(place: str, task: str) -> bool:
    return place in SETTINGS and task in TASKS and SETTINGS[place].has_water_source and SETTINGS[place].has_garden and task_at_risk(TASKS[task])


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if not reasonableness_gate(params.place, params.task):
        raise StoryError("This story needs a garden task that genuinely uses the bucket.")
    world = World(SETTINGS[params.place])

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child", meters={"joy": 0.0, "helpful": 0.0, "asking": 0.0, "relief": 0.0}, memes={"joy": 0.0, "helpful": 0.0, "asking": 0.0, "relief": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", meters={"joy": 0.0, "willing": 0.0, "pride": 0.0}, memes={"joy": 0.0, "willing": 0.0, "pride": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, role="parent"))
    bucket = world.add(Entity(id="bucket", type="bucket", label="bucket", phrase="a sturdy bucket", plural=False, owner="child", caretaker="parent", meters={"empty": 1.0, "heavy": 1.0, "water": 0.0, "steady": 0.0}, memes={"need": 0.0}))
    plant = world.add(Entity(id="plant", type="plant", label="little plant", phrase="a little thirsty plant", meters={"thirst": 1.0, "perk": 0.0}, memes={"thirst": 1.0, "hope": 0.0}))
    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        bucket=bucket,
        plant=plant,
        task=TASKS[params.task],
        setting=SETTINGS[params.place],
        at_water_source=SETTINGS[params.place].has_water_source,
    )
    return world


def tell(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    parent = world.get("parent")
    bucket = world.get("bucket")
    plant = world.get("plant")
    task = world.facts["task"]

    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"One bright morning, {child.id} noticed a little plant drooping in {world.setting.place}."
        f" The {bucket.label} sat nearby, but it was too heavy for one pair of small hands."
    )
    world.say(
        f'"Let\'s do it together," {helper.id} said, and {child.id} smiled because {helper.id} did not make the job feel big anymore.'
    )

    world.para()
    child.memes["asking"] += 1
    helper.memes["willing"] += 1
    world.say(
        f"{child.id} carried the {bucket.label} to the water source while {helper.id} steadied it from the other side."
        f" Together they filled {bucket.it()} carefully."
    )
    bucket.meters["water"] = 1.0
    bucket.meters["heavy"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then they walked back side by side and {task.verb}."
        f" The water was just enough, and {task.result}."
    )

    world.para()
    plant.meters["thirst"] = 0.0
    plant.meters["perk"] = 1.0
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1
    world.say(
        f"{parent.label_word.capitalize()} clapped softly from the doorway."
        f" {child.id} and {helper.id} set the {bucket.label} down together, and the little plant stood up straighter in the sun."
    )
    world.say(
        f"It was a small thing, but it felt like a big kind thing: two friends, one bucket, and a garden that looked happier by the minute."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    place = f["setting"].place
    return [
        f'Write a heartwarming story for a small child about teamwork with a bucket in {place}.',
        f"Tell a gentle story where {child.id} and a helper share one bucket to {task.verb} and make the garden better.",
        f'Write a short story that includes the word "bucket" and ends with two characters working together kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    bucket = f["bucket"]
    plant = f["plant"]
    task = f["task"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What made {child.id} need help in {place}?",
            answer=f"{child.id} wanted to {task.verb}, but the bucket was too heavy for one small child. {helper.id} made the job feel manageable by sharing the work.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} use the bucket together?",
            answer=f"{child.id} brought the {bucket.label} to the water source while {helper.id} steadied it, and together they filled it. That teamwork let them finish the task without anyone getting overwhelmed.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} smile at the end?",
            answer=f"{parent.label_word.capitalize()} saw that {child.id} and {helper.id} had worked kindly as a team, and the plant was no longer drooping. The happy ending showed that shared effort helped both the garden and the children.",
        ),
    ]
    if plant.meters.get("perk", 0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What changed after the water reached the plant?",
                answer=f"The plant perked up and looked brighter, so the garden felt cared for. That was the proof that the bucket teamwork worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"bucket"}
    out: list[QAItem] = []
    if "bucket" in tags:
        out.append(QAItem("What is a bucket for?", "A bucket is a container that can carry water, sand, or other things. People use it when they need to move something from one place to another."))
    if "water" in tags:
        out.append(QAItem("Why do plants need water?", "Plants need water to stay healthy and strong. Water helps them keep their leaves and stems from drooping."))
    if "garden" in tags:
        out.append(QAItem("What is a garden?", "A garden is a place where people grow flowers, vegetables, or small plants. It is a place that can be cared for and made beautiful."))
    if "care" in tags:
        out.append(QAItem("Why is helping with a chore kind?", "Helping with a chore is kind because it makes the job easier for everyone. It also shows that people can work together and care for one another."))
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={ {k: v for k, v in e.meters.items() if v} }")
        if e.memes:
            bits.append(f"memes={ {k: v for k, v in e.memes.items() if v} }")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_storyworlds() -> list[StoryParams]:
    out = []
    for place, task in valid_combos():
        out.append(
            StoryParams(
                place=place,
                task=task,
                child_name="Mia",
                child_gender="girl",
                helper_name="Noah",
                helper_gender="boy",
                parent_gender="mother",
            )
        )
    return out


CURATED = [
    StoryParams(place="garden", task="water_flower", child_name="Mia", child_gender="girl", helper_name="Noah", helper_gender="boy", parent_gender="mother"),
    StoryParams(place="backyard", task="fill_birdbath", child_name="Ben", child_gender="boy", helper_name="Ava", helper_gender="girl", parent_gender="father"),
    StoryParams(place="community_garden", task="wash_seedlings", child_name="Zoe", child_gender="girl", helper_name="Eli", helper_gender="boy", parent_gender="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming teamwork storyworld with a bucket.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    parent_gender = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        task=task,
        child_name=args.name or rng.choice(["Mia", "Ben", "Lily", "Noah", "Zoe", "Eli"]),
        child_gender=child_gender,
        helper_name=args.helper or rng.choice(["Noah", "Ava", "Eli", "Maya", "Owen", "Iris"]),
        helper_gender=helper_gender,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    world = build_world(params)
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


ASP_RULES = r"""
valid(P, T) :- place(P), task(T), water_place(P), garden_place(P), water_task(T).
helped :- child_asks, helper_joins, bucket_shared.
happy_end :- helped, plant_revived.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("water_place", pid))
        lines.append(asp.fact("garden_place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        if "water" in task.tags:
            lines.append(asp.fact("water_task", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid combos differ.")
            rc = 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: empty story.")
            rc = 1
        emit(sample, trace=False, qa=False)
    except Exception:
        traceback.print_exc()
        return 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for place, task in combos:
            print(f"  {place:18} {task}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.child_name} and {p.helper_name} in {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
