#!/usr/bin/env python3
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

TITLE_WORDS = ("twentieth", "conquer")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Task:
    id: str
    setting: str
    goal: str
    verb: str
    conflict: str
    lesson: str
    mess: str
    helper: str
    count: int


@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    partner_name: str
    gender: str
    partner_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, task: Task) -> None:
        self.task = task
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _m(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _mm(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


TASKS = {
    "paper_chain": Task(
        id="paper_chain",
        setting="classroom",
        goal="finish a long paper chain for the wall",
        verb="make the twentieth link",
        conflict="the tape kept sticking to the wrong fingers",
        lesson="they learned that teamwork makes a big job feel smaller",
        mess="scraps",
        helper="scissors and a ruler",
        count=20,
    ),
    "garden_beds": Task(
        id="garden_beds",
        setting="garden",
        goal="set up twenty little garden signs",
        verb="place the twentieth sign",
        conflict="one sign kept leaning in the dirt",
        lesson="they learned that teamwork helps a wobbly job stay steady",
        mess="soil",
        helper="a trowel and string",
        count=20,
    ),
    "cookie_tray": Task(
        id="cookie_tray",
        setting="kitchen",
        goal="carry a tray of treats to the table",
        verb="set out the twentieth cookie",
        conflict="the tray felt too full for one pair of hands",
        lesson="they learned that teamwork is a good way to conquer a hard job",
        mess="crumbs",
        helper="an oven mitt and a wide plate",
        count=20,
    ),
}


GIRL_NAMES = ["Maya", "Nora", "Lina", "Rosa", "Ivy", "Zoe"]
BOY_NAMES = ["Evan", "Noah", "Theo", "Milo", "Arlo", "Finn"]


def task_allows(task: Task, setting: str) -> bool:
    return task.setting == setting


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t.id) for s in SETTINGS for t in TASKS.values() if task_allows(t, s)]


SETTINGS = {
    "classroom": "the classroom",
    "garden": "the garden",
    "kitchen": "the kitchen",
}


def make_world(params: StoryParams) -> World:
    task = TASKS[params.task]
    world = World(task)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"focus": 0.0, "effort": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "frustration": 0.0, "teamwork": 0.0},
    ))
    partner = world.add(Entity(
        id=params.partner_name,
        kind="character",
        type=params.partner_gender,
        label=params.partner_name,
        meters={"focus": 0.0, "effort": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "frustration": 0.0, "teamwork": 0.0},
    ))
    project = world.add(Entity(
        id="project",
        type=task.id,
        label=task.goal,
        phrase=task.goal,
        owner=hero.id,
        meters={"pieces": 0.0, "mess": 0.0},
        memes={"done": 0.0},
    ))
    tools = world.add(Entity(
        id="tools",
        type="tools",
        label=task.helper,
        phrase=task.helper,
        owner=hero.id,
        meters={"use": 0.0},
    ))
    world.facts.update(hero=hero, partner=partner, project=project, tools=tools, task=task, setting=params.setting)
    return world


def story_text(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    task: Task = f["task"]
    setting = SETTINGS[f["setting"]]

    world.say(
        f"{hero.label} and {partner.label} were in {setting}, looking at {task.goal}."
    )
    world.say(
        f"They wanted to {task.verb}, because the room needed the last bit finished."
    )
    _mm(hero, "curiosity", 1)
    _mm(partner, "curiosity", 1)
    _m(hero, "effort", 1)
    _m(partner, "effort", 1)

    world.para()
    world.say(
        f"But {task.conflict}, and that made the work feel bigger than it should."
    )
    _mm(hero, "frustration", 1)
    _mm(partner, "frustration", 1)
    _m(f["project"], "mess", 1)
    _m(f["project"], "pieces", float(task.count - 1))
    world.say(
        f"{hero.label} wanted to hurry, while {partner.label} wanted to be careful."
    )
    world.say(
        f"For a moment, they both forgot that the job was something they had to conquer together."
    )

    world.para()
    world.say(
        f"Then {hero.label} pointed to {task.helper} and said they could split the steps."
    )
    _mm(hero, "teamwork", 1)
    _mm(partner, "teamwork", 1)
    _mm(hero, "joy", 1)
    _mm(partner, "joy", 1)
    world.say(
        f"One of them held the paper still, and the other made the {task.count}th part fit just right."
    )
    _m(f["project"], "pieces", 1)
    _m(f["project"], "mess", -1)
    _mm(f["project"], "done", 1)

    world.say(
        f"With both of them working side by side, they could conquer the tricky last step."
    )
    world.say(
        f"At the end, {task.lesson}, and {task.goal} looked bright and finished."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_text(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    return [
        f"Write a slice-of-life story about two children who try to {task.verb} and learn about teamwork.",
        f"Tell a gentle story where a small conflict about {task.goal} leads to a lesson learned.",
        f"Write a child-friendly story that includes the words '{TITLE_WORDS[0]}' and '{TITLE_WORDS[1]}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    task: Task = f["task"]
    setting = SETTINGS[f["setting"]]
    return [
        QAItem(
            question=f"Where were {hero.label} and {partner.label} working?",
            answer=f"They were in {setting}, trying to finish {task.goal}.",
        ),
        QAItem(
            question=f"What was the hard part of the story?",
            answer=f"The hard part was that {task.conflict}, so the job felt stuck for a moment.",
        ),
        QAItem(
            question=f"What did they learn by the end?",
            answer=f"They learned that teamwork helps them conquer a hard job together.",
        ),
        QAItem(
            question=f"Which part of the task did they finish last?",
            answer=f"They finished the {task.count}th part, which was {task.verb}.",
        ),
    ]


WORLD_QA = [
    QAItem(question="What does teamwork mean?", answer="Teamwork means people work together and help one another do a job."),
    QAItem(question="What is a conflict?", answer="A conflict is a small problem or disagreement that makes things hard for a little while."),
    QAItem(question="What does it mean to conquer a task?", answer="To conquer a task means to get through a hard job by not giving up."),
    QAItem(question="What is a lesson learned?", answer="A lesson learned is something a character understands after what happens in the story."),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
setting(classroom).
setting(garden).
setting(kitchen).

task(paper_chain). task(garden_beds). task(cookie_tray).

allowed(classroom,paper_chain).
allowed(garden,garden_beds).
allowed(kitchen,cookie_tray).

twentieth_goal(T) :- task(T).
has_conflict(T) :- task(T).
teamwork_solution(T) :- task(T), allowed(S,T).

valid_story(S,T) :- allowed(S,T), twentieth_goal(T), has_conflict(T), teamwork_solution(T).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        lines.append(asp.fact("allowed", t.setting, t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about teamwork, conflict, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--name")
    ap.add_argument("--partner-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting and args.task:
        if (args.setting, args.task) not in combos:
            raise StoryError("No reasonable story matches that setting and task.")
    combos = [
        c for c in combos
        if (not args.setting or c[0] == args.setting)
        and (not args.task or c[1] == args.task)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, task = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner_name = args.partner_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    return StoryParams(setting=setting, task=task, name=name, partner_name=partner_name, gender=gender, partner_gender=partner_gender)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
    StoryParams(setting="classroom", task="paper_chain", name="Maya", partner_name="Noah", gender="girl", partner_gender="boy"),
    StoryParams(setting="garden", task="garden_beds", name="Evan", partner_name="Lina", gender="boy", partner_gender="girl"),
    StoryParams(setting="kitchen", task="cookie_tray", name="Ivy", partner_name="Theo", gender="girl", partner_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(sorted(asp_valid_combos()))
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
            header = f"### {p.name} and {p.partner_name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
