#!/usr/bin/env python3
"""
storyworlds/worlds/cardinal_difficult_rhyme_magic_slice_of_life.py
===================================================================

A small slice-of-life story world about a child, a cardinal, a difficult task,
and a little bit of rhyme-magic.

Premise:
- A child is trying to finish a difficult everyday task.
- A bright cardinal appears during a calm, ordinary day.
- A gentle rhyme and a small bit of magic help the child turn frustration into
  steady progress.
- The ending proves the change by showing the task finished and the mood
  lifted.

This world is intentionally small and constraint-checked. The story is built
from the simulated state, not from a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wearer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    difficulty: str
    progress_gain: float
    frustration_gain: float
    completion_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    helps_task: set[str]
    rhyme_line: str
    magic_line: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", detail="Sunlight lay across the table, and a dish towel hung nearby."),
    "laundry": Setting(place="the laundry room", detail="The warm room smelled like soap, and a basket waited by the door."),
    "porch": Setting(place="the front porch", detail="The porch was quiet, with a potted plant and a small wooden step."),
}

TASKS = {
    "folding": Task(
        id="folding",
        verb="fold the towels",
        gerund="folding towels",
        difficulty="difficult",
        progress_gain=1.0,
        frustration_gain=1.0,
        completion_line="The towels sat in neat little squares.",
        tags={"towels", "home"},
    ),
    "sorting": Task(
        id="sorting",
        verb="sort the buttons",
        gerund="sorting buttons",
        difficulty="difficult",
        progress_gain=1.0,
        frustration_gain=1.0,
        completion_line="The buttons were lined up by color.",
        tags={"buttons", "home"},
    ),
    "watering": Task(
        id="watering",
        verb="water the plant",
        gerund="watering the plant",
        difficulty="difficult",
        progress_gain=1.0,
        frustration_gain=0.8,
        completion_line="The little plant stood straighter in its pot.",
        tags={"plant", "home"},
    ),
}

CHARMS = {
    "cardinal_song": Charm(
        id="cardinal_song",
        label="cardinal song",
        phrase="a bright red cardinal",
        effect="focus",
        helps_task={"folding", "sorting", "watering"},
        rhyme_line="Red bird, bright bird, sing a tiny tune.",
        magic_line="The rhyme made the busy hands feel steady and light.",
        tags={"cardinal", "rhyme", "magic"},
    ),
    "window_rhyme": Charm(
        id="window_rhyme",
        label="window rhyme",
        phrase="a soft rhyme from the window",
        effect="calm",
        helps_task={"folding", "sorting"},
        rhyme_line="Breathe in, breathe out, and let your shoulders rest.",
        magic_line="The rhyme tucked the worry away for a little while.",
        tags={"rhyme", "magic"},
    ),
}

CHILD_NAMES = ["Maya", "Nora", "Lena", "Theo", "Owen", "Sage", "Iris", "Noah"]
PARENT_NAMES = ["Mom", "Dad"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    charm: str
    name: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_supported(setting: Setting, task: Task) -> bool:
    return True  # all tasks can happen in the listed small settings


def charm_compatible(task: Task, charm: Charm) -> bool:
    return task.id in charm.helps_task


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for c in CHARMS:
                if task_supported(SETTINGS[s], TASKS[t]) and charm_compatible(TASKS[t], CHARMS[c]):
                    out.append((s, t, c))
    return out


def explain_rejection(task: Task, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} does not help with {task.gerund}. "
        f"The magical rhyme has to fit the task in a believable slice-of-life way.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
compatible(S, T, C) :- setting(S), task(T), charm(C),
                       helps(C, T), supports(S, T).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("difficulty", tid, task.difficulty))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tags", tid, tag))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for task_id in sorted(charm.helps_task):
            lines.append(asp.fact("helps", cid, task_id))
        for tag in sorted(charm.tags):
            lines.append(asp.fact("tags", cid, tag))
    for sid in SETTINGS:
        for tid in TASKS:
            lines.append(asp.fact("supports", sid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    charm = CHARMS[params.charm]

    world = World(setting=params.setting)
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent"))
    bird = world.add(Entity(id="cardinal", kind="creature", type="cardinal", label="cardinal"))

    child.meters["work"] = 0.0
    child.meters["progress"] = 0.0
    child.memes["frustration"] = 0.0
    child.memes["joy"] = 0.0
    bird.meters["spark"] = 0.0
    bird.memes["gentleness"] = 0.0

    world.facts.update(
        child=child,
        parent=parent,
        bird=bird,
        task=task,
        charm=charm,
        setting=setting,
    )

    world.say(f"{child.id} was in {setting.place}. {setting.detail}")
    world.say(f"{child.id} had a {task.difficulty} job to {task.verb}, and {child.pronoun('subject')} kept losing the rhythm.")
    world.say(f"{parent.id} was nearby, giving patient smiles instead of hurry.")

    world.para()
    world.say(f"At the window, a bright red cardinal hopped onto the sill.")
    world.say(f"It looked like the little bird had brought {charm.phrase} to the day.")
    world.say(charm.rhyme_line)

    # The rhyme and cardinal calm the child down.
    if charm.id == "cardinal_song":
        bird.meters["spark"] += 1
        bird.memes["gentleness"] += 1
    child.memes["frustration"] += 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.meters["progress"] += task.progress_gain * 0.4

    world.say(charm.magic_line)
    world.say(f"{child.id} took a breath, checked the stack again, and tried once more.")

    # Progress loop: if charm is compatible, enough progress accumulates to finish.
    if charm_compatible(task, charm):
        child.meters["progress"] += task.progress_gain
        child.memes["frustration"] = max(0.0, child.memes["frustration"] - 1.0)
        child.memes["joy"] += 1
        world.say(f"With the little rhyme in mind, {child.id}'s hands found an easier way.")
        world.say(task.completion_line)
        world.say(f"{parent.id} smiled and said that the hard part was over now.")
        world.say(f"{child.id} looked at the tidy work and felt proud of the small finish.")
    else:
        world.say(f"The day stayed a little wobbly, and the task was still unfinished.")

    world.facts["done"] = child.meters["progress"] >= THRESHOLD
    world.facts["frustrated"] = child.memes["frustration"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    charm: Charm = f["charm"]
    child: Entity = f["child"]
    return [
        f'Write a short slice-of-life story for a young child where {child.id} has a {task.difficulty} job to {task.verb} and a cardinal appears.',
        f"Tell a gentle story that includes a rhyme and a little magic, helping {child.id} finish {task.gerund}.",
        f'Write a calm story about {child.id}, a cardinal, and "{task.difficulty}" work that ends with a tidy result.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    task: Task = f["task"]
    charm: Charm = f["charm"]

    return [
        QAItem(
            question=f"What difficult job did {child.id} have to do?",
            answer=f"{child.id} had to {task.verb}. It was a {task.difficulty} little task, so it took patience.",
        ),
        QAItem(
            question=f"What bird appeared during the story?",
            answer="A bright red cardinal appeared at the window and helped make the day feel calmer.",
        ),
        QAItem(
            question=f"How did the rhyme and magic help {child.id}?",
            answer=(
                f"The rhyme and magic helped {child.id} slow down, breathe, and keep going. "
                f"That made the hard job feel easier and let the work get finished."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=(
                f"The story ended with {child.id} finishing the task and feeling proud. "
                f"The work looked tidy, and {parent.id} was smiling nearby."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cardinal?",
            answer="A cardinal is a small bird with bright red feathers.",
        ),
        QAItem(
            question="What can a rhyme do in a story?",
            answer="A rhyme can sound playful and help a story feel calm, memorable, or fun.",
        ),
        QAItem(
            question="What does magic mean in a gentle slice-of-life story?",
            answer="In a gentle story, magic can mean a tiny special help that makes ordinary life a little easier.",
        ),
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    lines.append(f"  facts: done={world.facts.get('done')} frustrated={world.facts.get('frustrated')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.charm:
        task = TASKS[args.task]
        charm = CHARMS[args.charm]
        if not charm_compatible(task, charm):
            raise StoryError(explain_rejection(task, charm))

    combos = [
        c for c in valid_story_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.task is None or c[1] == args.task)
        and (args.charm is None or c[2] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, task, charm = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting=setting, task=task, charm=charm, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", task="folding", charm="cardinal_song", name="Maya", parent="Mom"),
    StoryParams(setting="laundry", task="sorting", charm="window_rhyme", name="Theo", parent="Dad"),
    StoryParams(setting="porch", task="watering", charm="cardinal_song", name="Iris", parent="Mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life story world about a cardinal, a difficult task, rhyme, and a little magic."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (setting, task, charm) combos:")
        for item in combos:
            print("  ", item)
        return

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
            header = f"### {p.name}: {p.task} in {p.setting} (charm: {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
