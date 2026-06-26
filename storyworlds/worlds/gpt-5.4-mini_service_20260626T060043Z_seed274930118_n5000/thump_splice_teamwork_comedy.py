#!/usr/bin/env python3
"""
Standalone storyworld: a comedy about teamwork, a thumping problem, and a splice repair.

Seed premise:
- A small team hears a funny thump.
- They discover something is torn and needs a splice.
- They work together, each using a different skill, and the fix becomes the ending image.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the art room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    name: str
    symptom: str
    action: str
    repair: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    can_fix: set[str]
    prep: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sound: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.sound = self.sound
        return clone


def _r_sound(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("thump", 0.0) < THRESHOLD:
            continue
        sig = ("sound", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["surprise"] = actor.memes.get("surprise", 0.0) + 1
        out.append(f"Thump! went the strange little noise.")
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    for thing in world.entities.values():
        if thing.kind != "thing":
            continue
        if thing.meters.get("broken", 0.0) < THRESHOLD:
            continue
        if thing.meters.get("fixed", 0.0) >= THRESHOLD:
            continue
        sig = ("fixed", thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        thing.meters["fixed"] = 1.0
        out.append(f"The broken piece was finally whole again.")
    return out


CAUSAL_RULES = [_r_sound, _r_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def predict_fix(world: World, actor: Entity, task: Task) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["thump"] = 1.0
    return task.id in TASKS and bool(select_tool(task))


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.can_fix:
            return tool
    return None


def introduce_team(world: World, team: list[Entity]) -> None:
    names = ", ".join(e.id for e in team[:-1]) + f", and {team[-1].id}"
    world.say(f"{names} were a tiny team who liked solving problems together.")


def setup_task(world: World, team: list[Entity], task: Task) -> None:
    world.say(
        f"In {world.setting.place}, the team heard a funny {task.keyword} sound, "
        f"like something sneezing through a shoe box."
    )
    world.say(
        f"They found the prop with a rip so awkward it looked embarrassed."
    )


def do_thump(world: World, actor: Entity) -> None:
    actor.meters["thump"] = actor.meters.get("thump", 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=True)


def explain_problem(world: World, task: Task) -> None:
    world.say(
        f"It had a {task.symptom}, and every wobble made it go {task.keyword} again."
    )


def brainstorm(world: World, team: list[Entity], task: Task) -> None:
    world.say(
        f"{team[0].id} pointed. {team[1].id} fetched the tape. {team[-1].id} held the ends still."
    )
    world.say("Nobody bossed anybody around, which was rare and impressive.")


def splice_repair(world: World, team: list[Entity], task: Task, tool: Tool, prop: Entity) -> None:
    prop.meters["broken"] = 1.0
    world.say(
        f"They used {tool.label} to {task.repair}, and {team[0].id} said, "
        f"'"This is the fanciest {task.keyword} I have ever heard."'
    )
    prop.meters["fixed"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {team[1].id} pressed the seam flat while {team[-1].id} gave it a proud little nod."
    )
    prop.meters["fixed"] = 1.0
    propagate(world, narrate=True)


def ending(world: World, prop: Entity, task: Task) -> None:
    world.say(
        f"At the end, the prop was strong, smooth, and quiet. No more {task.keyword}. "
        f"Just a neat splice and four grins."
    )


SETTINGS = {
    "art_room": Setting(place="the art room", affords={"splice"}),
    "workbench": Setting(place="the workbench corner", affords={"splice"}),
    "stage": Setting(place="the little stage", affords={"splice"}),
}

TASKS = {
    "banner": Task(
        id="banner",
        name="the paper banner",
        symptom="long tear",
        action="fix the torn banner",
        repair="splice the tear with tape",
        keyword="thump",
        tags={"thump", "paper", "tape"},
    ),
    "sock_puppet": Task(
        id="sock_puppet",
        name="the sock puppet",
        symptom="split seam",
        action="fix the puppet",
        repair="splice the seam with a neat strip of cloth tape",
        keyword="thump",
        tags={"thump", "cloth", "tape"},
    ),
    "kite_tail": Task(
        id="kite_tail",
        name="the kite tail",
        symptom="dangly rip",
        action="fix the tail",
        repair="splice the ribbons back together",
        keyword="thump",
        tags={"thump", "ribbon", "knot"},
    ),
}

TOOLS = [
    Tool(id="tape", label="bright tape", can_fix={"banner", "sock_puppet"}, prep="grab the tape roll"),
    Tool(id="cloth_tape", label="cloth tape", can_fix={"sock_puppet"}, prep="find the cloth tape"),
    Tool(id="string", label="soft string", can_fix={"kite_tail"}, prep="bring the soft string"),
]

NAMES = ["Milo", "Nia", "Pip", "June", "Ollie", "Bea", "Toby", "Rae"]
TRAITS = ["cheerful", "curious", "silly", "quick", "kind"]


@dataclass
class StoryParams:
    place: str
    task: str
    name1: str
    name2: str
    name3: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            if select_tool(TASKS[task_id]):
                combos.append((place, task_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy teamwork storyworld with a thump and a splice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    place, task = rng.choice(combos)
    names = [args.name1, args.name2, args.name3]
    picked = [n or rng.choice(NAMES) for n in names]
    if len(set(picked)) < 3:
        raise StoryError("Please choose three different team names.")
    return StoryParams(place=place, task=task, name1=picked[0], name2=picked[1], name3=picked[2],
                       trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    a = world.add(Entity(id=params.name1, kind="character", type="girl"))
    b = world.add(Entity(id=params.name2, kind="character", type="boy"))
    c = world.add(Entity(id=params.name3, kind="character", type="girl"))
    prop = world.add(Entity(id="prop", type=TASKS[params.task].name, label=TASKS[params.task].name, plural=False))
    task = TASKS[params.task]
    tool = select_tool(task)

    introduce_team(world, [a, b, c])
    world.para()
    setup_task(world, [a, b, c], task)
    do_thump(world, a)
    explain_problem(world, task)
    world.para()
    brainstorm(world, [a, b, c], task)
    if tool is None:
        raise StoryError("No reasonable tool exists for this task.")
    world.say(f"{b.id} dashed off and came back with {tool.label}.")
    splice_repair(world, [a, b, c], task, tool, prop)
    world.para()
    ending(world, prop, task)

    world.facts.update(task=task, tool=tool, prop=prop, team=[a, b, c], params=params)
    story = world.render()
    return StorySample(params=params, story=story, prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    return [
        f'Write a funny teamwork story for a child that includes the word "{task.keyword}".',
        f"Tell a comic story where three friends hear a {task.keyword} and fix {task.name} together.",
        f"Write a short story about a team that uses a splice to repair something noisy and broken.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    team = f["team"]
    tool: Tool = f["tool"]
    prop: Entity = f["prop"]
    return [
        QAItem(
            question=f"What did the team hear in {world.setting.place}?",
            answer=f"They heard a funny {task.keyword} noise that came from {prop.label}.",
        ),
        QAItem(
            question=f"What did they use to fix {prop.label}?",
            answer=f"They used {tool.label} to {task.repair}.",
        ),
        QAItem(
            question=f"How did the three friends solve the problem?",
            answer=f"They worked together: one spotted the problem, one brought the tool, and one held the piece still.",
        ),
        QAItem(
            question=f"What was the ending like after the fix?",
            answer=f"The ending was calm and funny at the same time, because {prop.label} was smooth, strong, and quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splice?",
            answer="A splice is a way to join two broken parts together so they hold as one again.",
        ),
        QAItem(
            question="Why can tape help with a torn paper prop?",
            answer="Tape can hold torn paper together for a while, which makes it useful for a quick repair.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share jobs to finish something together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_valid(P, T) :- place(P), task(T), afford(P, T), has_tool(T).
teamwork(T) :- task_valid(_, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for task in sorted(setting.affords):
            lines.append(asp.fact("afford", pid, task))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("has_tool", tid) if select_tool(task) else asp.fact("no_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show task_valid/2."))
    return sorted(set(asp.atoms(model, "task_valid")))


def asp_verify() -> int:
    py = set((p, t) for p, t in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(place="art_room", task="banner", name1="Milo", name2="Nia", name3="Pip", trait="cheerful"),
    StoryParams(place="workbench", task="sock_puppet", name1="June", name2="Ollie", name3="Bea", trait="silly"),
    StoryParams(place="stage", task="kite_tail", name1="Rae", name2="Toby", name3="Luna", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show task_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show task_valid/2."))
        print(sorted(set(asp.atoms(model, "task_valid"))))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
