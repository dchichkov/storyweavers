#!/usr/bin/env python3
"""
A bedtime-story world about a small folk village, quiet merit, and one gentle surprise.

The world is built around a child who hopes to earn a little merit by helping the folk
in their homes before sleep. The turn comes when a surprise appears: the lost lantern,
the hidden ribbon, or the soft lullaby book, and the child must choose a kind action
that proves their merit in a concrete, state-driven way.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "child", "adult", "folk", "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the village lane"
    quiet: bool = True
    folk: str = "the folk"


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    small_help: str
    merit_gain: float
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    child_type: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.surprised: bool = False
        self.merit_total: float = 0.0
        self.bedtime: bool = True

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


TASKS = {
    "tidy": Task(
        id="tidy",
        verb="tidy the little room",
        gerund="tidying the little room",
        small_help="swept the crumbs into a neat line",
        merit_gain=1.0,
        surprise="a tucked-away bookmark",
        tags={"tidy", "room"},
    ),
    "tea": Task(
        id="tea",
        verb="set out tea cups",
        gerund="setting out tea cups",
        small_help="placed each cup beside a soft napkin",
        merit_gain=1.0,
        surprise="a warm cinnamon bun",
        tags={"tea", "cups"},
    ),
    "shelf": Task(
        id="shelf",
        verb="put books on the shelf",
        gerund="putting books on the shelf",
        small_help="stacked the books by size",
        merit_gain=1.0,
        surprise="a hidden picture card",
        tags={"books", "shelf"},
    ),
    "blanket": Task(
        id="blanket",
        verb="fluff the bedtime blanket",
        gerund="fluffing the bedtime blanket",
        small_help="shook the blanket until it looked like a cloud",
        merit_gain=1.0,
        surprise="a stitched star on the corner",
        tags={"blanket", "bedtime"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a little brass lantern", region="hands", fragile=True),
    "ribbon": Prize(label="ribbon", phrase="a blue ribbon", region="hair", fragile=True),
    "book": Prize(label="book", phrase="a sleepy picture book", region="hands", fragile=False),
    "cup": Prize(label="cup", phrase="a tiny teacup", region="hands", fragile=True),
}

SETTINGS = {
    "lane": Setting(place="the village lane", quiet=True, folk="the folk"),
    "cottage": Setting(place="the cottage room", quiet=True, folk="the folk"),
    "hall": Setting(place="the lantern hall", quiet=True, folk="the folk"),
}

NAMES = ["Mina", "Toby", "Nell", "Iris", "Robin", "Pip", "Luna", "Ezra"]
HELPERS = ["grandmother", "grandfather", "aunt", "uncle", "neighbor"]
CHILD_TYPES = ["girl", "boy"]


def stable_choice(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def current_merit(world: World) -> float:
    return sum(e.memes.get("merit", 0.0) for e in world.entities.values())


def build_scene(setting: Setting, task: Task, prize: Prize, name: str, child_type: str, helper: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="child", type=child_type, label=name))
    adult = world.add(Entity(id="Helper", kind="adult", type=helper, label=f"the {helper}"))
    treasure = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize.label,
        label=prize.label,
        phrase=prize.phrase,
        owner=child.id,
        caretaker=adult.id,
    ))
    child.memes["merit"] = 0.0
    child.memes["hope"] = 1.0
    adult.memes["care"] = 1.0
    world.facts.update(child=child, adult=adult, prize=treasure, task=task, setting=setting)
    return world


def narrate_opening(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    prize: Entity = f["prize"]
    task: Task = f["task"]
    setting: Setting = f["setting"]
    world.say(
        f"On a quiet night, {child.id} lived near {setting.place}, where the folk moved softly "
        f"like whispers under the moon."
    )
    world.say(
        f"{child.id} wanted to earn a little merit by {task.gerund}, and {adult.label} had set out {prize.phrase} "
        f"to make the evening feel extra gentle."
    )


def do_task(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    child.meters[task.id] = child.meters.get(task.id, 0.0) + 1.0
    child.memes["merit"] += task.merit_gain
    world.merit_total = current_merit(world)
    world.say(
        f"{child.id} began {task.gerund}, and the small work made the room feel calmer."
    )
    world.say(f"{child.id} {task.small_help}, and the folk nearby smiled in the candlelight.")


def surprise_turn(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    prize: Entity = f["prize"]
    task: Task = f["task"]
    if task.id in world.fired:
        return
    world.fired.add((task.id, "surprise"))
    world.surprised = True
    child.memes["surprise"] = 1.0
    world.say(
        f"Then came a little surprise: inside {prize.phrase}, {task.surprise} was hidden where nobody had noticed it."
    )
    world.say(
        f"{child.id} blinked, then held it carefully, because some surprises feel best when they are treated like tiny treasures."
    )


def resolve(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    prize: Entity = f["prize"]
    task: Task = f["task"]
    child.memes["content"] = 1.0
    child.memes["merit"] += 1.0
    world.merit_total = current_merit(world)
    world.say(
        f"{adult.label} said that the surprise was a reward for {child.id}'s kind work, and the two of them sat by the warm lamp."
    )
    world.say(
        f"{child.id} tucked the treasure beside {prize.label}, and the folk in the village lane settled down, happy and sleepy."
    )
    world.say(
        f"By bedtime, {child.id} had not only finished {task.verb}, but had also earned a quiet merit that felt warm in the heart."
    )


def tell(setting: Setting, task: Task, prize: Prize, name: str, child_type: str, helper: str) -> World:
    world = build_scene(setting, task, prize, name, child_type, helper)
    narrate_opening(world)
    world.para()
    do_task(world)
    surprise_turn(world)
    world.para()
    resolve(world)
    return world


def make_story_question(child: Entity, adult: Entity, prize: Entity, task: Task, setting: Setting) -> list[QAItem]:
    return [
        QAItem(
            question=f"Why did {child.id} try to {task.verb} near {setting.place}?",
            answer=f"{child.id} wanted to earn a little merit, and {adult.label} had set out {prize.phrase} for the bedtime evening.",
        ),
        QAItem(
            question=f"What surprise did {child.id} find while {child.id} was {task.gerund}?",
            answer=f"{child.id} found {task.surprise} hidden inside {prize.phrase}.",
        ),
        QAItem(
            question=f"What changed by the end of the story for {child.id}?",
            answer=f"{child.id} finished the small job, helped the folk, and felt warm and proud because the merit was earned quietly.",
        ),
    ]


def make_world_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is merit?",
            answer="Merit is a kind of good worth you earn when you do something thoughtful, helpful, or brave.",
        ),
        QAItem(
            question="Why do bedtime stories often feel calm?",
            answer="Bedtime stories often feel calm because they use soft places, gentle actions, and quiet endings that help listeners settle down.",
        ),
        QAItem(
            question="What are the folk in a story?",
            answer="The folk are the people in the story world, often a small group who live near one another and share a home or village.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that appears or happens, making the story turn in a new way.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.quiet:
            lines.append(asp.fact("quiet_place", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("merit_gain", tid, int(t.merit_gain)))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Prize) :- setting(Place), task(Task), prize(Prize).
quiet_bedtime(Place) :- quiet_place(Place).
surprise_story(Place, Task, Prize) :- valid(Place, Task, Prize), quiet_bedtime(Place), merit_gain(Task, 1), region(Prize, hands).
#show valid/3.
#show surprise_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for p in SETTINGS:
        for t in TASKS:
            for pr in PRIZES:
                out.append((p, t, pr))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gate")
    if a - b:
        print("only in clingo:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    prize: Entity = f["prize"]
    setting: Setting = f["setting"]
    return [
        f'Write a gentle bedtime story about a child named {child.id} who wants to earn merit by {task.gerund}.',
        f"Tell a quiet story where the folk near {setting.place} notice a small surprise hidden in {prize.phrase}.",
        f'Write a bedtime-style story that includes "folk", "merit", and a surprise that changes the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return make_story_question(f["child"], f["adult"], f["prize"], f["task"], f["setting"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.task and args.task not in TASKS:
        raise StoryError("Unknown task.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    places = [args.place] if args.place else list(SETTINGS)
    tasks = [args.task] if args.task else list(TASKS)
    prizes = [args.prize] if args.prize else list(PRIZES)
    combos = [(p, t, pr) for p in places for t in tasks for pr in prizes]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, prize = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, task=task, prize=prize, name=name, child_type=child_type, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.name, params.child_type, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=make_world_qa(),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  surprise={world.surprised} merit_total={world.merit_total}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about folk, merit, and a gentle surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper", choices=HELPERS)
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


CURATED = [
    StoryParams(place="lane", task="tidy", prize="book", name="Mina", child_type="girl", helper="grandmother"),
    StoryParams(place="cottage", task="tea", prize="cup", name="Toby", child_type="boy", helper="aunt"),
    StoryParams(place="hall", task="blanket", prize="ribbon", name="Nell", child_type="girl", helper="uncle"),
]


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
        print(asp_program("#show valid/3.\n#show surprise_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show surprise_story/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos")
        for row in vals:
            print(" ", row)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = rng_base + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
